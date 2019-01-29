#!/usr/bin/env python

'''ner.py : scripts related to named entity recognition and associated cleaning
'''

import pandas as pd
import re
import spacy
from sys import argv

# processed CSV with marker text and hmdb category labels
MARKER_CSV = '../data/190121-all-markers-with-cats.csv'

# various processing strings called in functions below, put here for convenience
# regex to perform replacements on raw marker text, in this order
STDIZE_TEXT = [(r"\.\s+\.(\s+\.)*", "."), # one or more alternating "." " "
               (r"\.(\s)+", ". "), # multiple spaces after period
               (r"\n", ""), # carriage returns
               (r"(\s)+", " "), # remaining multiple spaces
               (r" \.", "."), # ' .' artifacts
               (r"\?\.", "?"), # "?." artifacts
              ]
 
ENTS_TO_DROP = ['limes', 'st', 'rev', "jr", "sr", "john", "wm",
                  "alexander", "albert", "the city of",
                  "the republic of", "sun", 'today', 'daily',
                  'years', 'war', 'NW', 'city', 'east', "west", 'south',
                  'north', 'day', 'first', '–',
                  'mon sun', '©washington post', '°F', 'american',
                  'americans', "sunday", "cultural tourism DC",
                  "the District after", "CulturalTourismDC.org"]

LABELS_TO_USE = ['DATE', 'EVENT', 'FAC', 'GPE', 'LANGUAGE', 'LAW',
       'LOC', 'NORP', 'ORG', 'PERSON',
       'PRODUCT', 'WORK_OF_ART']

CLEAN_ENTITIES_RE = [(r"([^\w\d])+$|\_$", ""), # terminal non-word or non-digit
                     (r"^the |^an |^a |^ ", ""), # starting articles or space
                     (r"\'s$", ""), # ending possessive
                     (r'^ill\.$', 'illinois'),
                     (r'^mass\.$', 'massachusetts'),
                     (r'^md\.$', 'maryland'),
                     (r'^mo\.$', 'missouri'),
                     (r'^n\.h\.$', 'new hampshire'),
                     (r'^n\.y\.$', 'new york'),
                     (r'^nc$', 'north carolina'),
                     (r'^nj$', 'new jersey'),
                     (r'^nv$', 'nevada'),
                     (r'^ny$', 'new york'),
                     (r'^nev\.$', 'nevada'),
                     (r'^pa$', 'pennsylvania'),
                     (r'^pa\.$', 'pennsylvania'),
                     (r'^perú$', 'peru'),
                     (r'^va\.$', 'virginia'),
                     (r"([\[\]\(\)\{\}\:\"\'\.])+",""), # ( ) [ ] { } : " ' . -- any \. dependent regex before here!
                     (r"-", " "),
                     (r"(?:about|around|late|early|middle|mid|from|c\.?|the year) (\d\d\d\d)", r"\1"), # approximate years
                     (r"(the end of the|the turn of the) ", ""),
                     (r"first world war|great war", "world war i"),
                     (r"second world war", "world war ii"),
                     (r'^american revolution.+', 'american revolution'),
                     (r'^civil war.+', 'civil war'),
                     (r'^anacostia.+', 'anacostia'),
                     (r'^georgetown.+', 'georgetown'),
                     (r'^rock creek.+', 'rock creek'),
                     (r'^potomac.+', 'potomac'),
                     (r'(washington, dc|district of columbia|district of colombia|^dc$|^DC$|^washington$|^city of washington$)', 'washington dc'),
                     (r'(^us$|^usa$|^US$|^united states of america$)', 'united states'),
                     ('sally ride dr ride', 'sally ride'),
                     (r'(.+)(?:memorial$|park$|building$|residence$)', r'\1'),
                     ('^lenfant$', 'pierre lenfant'),
                     (r'(^abe$|^lincoln$|^abe lincoln$)', 'abraham lincoln'),
                     ('susan b anthony 1820   1906', 'susan b anthony'),
                     (r'^latin american$', 'latino'),
                     (r'^latinos$', 'latino'),
                     (r'^african americans$', 'african american'),
                     (r'^afro american$', 'african american'),
                     (r'^black american$', 'african american'),
                     (r'^scotsmen$', 'scottish'),
                     (r'^(frenchman|frenchmen)$', 'french'),
                     (r'^englishman$', 'english'),
                    ] 

LABELS_DROP_STRINGS = [r' avenue$', r' $ave', r' street$', r' st$',
                       r' road$', ' rd$', ' lane$', ' ln$',
                       r' (?:avenue|ave|st|street) (?:nw|sw|se|ne)$',
                       r'^\d+ to \d+']

def standardize_text(df, col_name):
    text_series = df[col_name].copy()
    for find_re, replace_str in STDIZE_TEXT:
        text_series = text_series.str.replace(find_re, replace_str)
    return text_series

def create_df_ent(df, nlp, remove_doc_dups=False):
    ents_labels = []
    ents_texts = []
    ents_markers = []
    ents_ids = []
    if remove_doc_dups:
        print('removing duplicate entities from docs')
    else:
        print('preserving duplicate entities in docs')
    for i, row in enumerate(df.itertuples()):
        doc = nlp(row.text_clean)
        ent_text_label_tuples = [(ent.text, ent.label_) for ent in doc.ents]
        if remove_doc_dups:
            # use set to remove duplicates. note that a set of (ent.text,
            # ent.label_) will remove dupes. set of just ents themselves will
            # not, since ents are distinct objects (each refers to a specific
            # location in the source doc)
            tuples_to_iterate = set(ent_text_label_tuples)
        else:
            tuples_to_iterate = ent_text_label_tuples
        for (ent_text, ent_label) in set(ent_text_label_tuples):
            ents_labels.append(ent_label)
            ents_texts.append(ent_text)
            ents_markers.append(i)
            ents_ids.append(row.marker_id)

    df_ent = pd.DataFrame({'label': ents_labels, 'text': ents_texts,
                           'marker_idx': ents_markers, 'marker_id': ents_ids})
    return df_ent

def filter_df_ent_by_label(df_ent):
    df_ent = df_ent[df_ent.label.isin(LABELS_TO_USE)]
    return df_ent

def df_ent_std_caps(df_ent):
    # convert all to lower case exccept entities all in caps
    df_ent['allcaps'] = df_ent['text'].str.upper() == df_ent['text']
    df_ent.loc[df_ent['allcaps']==False, 'text'] = df_ent.loc[df_ent['allcaps']==False, 'text'].str.lower()
    # clean up allcaps
    df_ent = df_ent.drop('allcaps', axis=1)
    return df_ent

def clean_entities(df_ent):
    for find_re, replace_re in CLEAN_ENTITIES_RE:
        df_ent['text'] = df_ent['text'].str.replace(find_re, replace_re)
    # in case added whitespace somehwere above
    df_ent['text'] = df_ent['text'].str.strip()
    return df_ent

def drop_flagged_labels(df_ent):
    df_ent = df_ent.loc[~df_ent.text.isin(ENTS_TO_DROP)]
    return df_ent

def drop_labels_regex(df_ent):
    labels_drop_regex = "|".join(LABELS_DROP_STRINGS)

    df_ent = df_ent.loc[~df_ent.text.str.contains(labels_drop_regex)]
    return df_ent

def ne_pipeline(csv_out=None):
    # combine steps from MARKER_CSV to df_ent of entities
    print("importing {}".format(MARKER_CSV))
    df = pd.read_csv(MARKER_CSV).query('cty=="washington_dc"')
    
    print("cleaning marker text")
    df['text_clean'] = standardize_text(df, 'text')

    print('loading language model')
    nlp = spacy.load("en_core_web_lg")

    print("performing NER on cleaned marker text")
    df_ent = create_df_ent(df, nlp)

    print("cleaning up named entities")
    df_ent = filter_df_ent_by_label(df_ent)
    df_ent = df_ent_std_caps(df_ent)
    df_ent = clean_entities(df_ent)
    df_ent = drop_flagged_labels(df_ent)
    df_ent = drop_labels_regex(df_ent)

    print("finished obtaining named entities. sample entries:")
    print(df_ent.head())

    if csv_out is not None:
        print('writing output to {}'.format(csv_out))
        df_ent.to_csv(csv_out)

    return df_ent

if __name__ == '__main__':
    print("running ner.py from command line")
    if len(argv)>1:
        csv_out = argv[1]
    else:
        csv_out = None
    ne_pipeline(csv_out)
    print('ner.py: done.')
