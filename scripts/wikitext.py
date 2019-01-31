#!/usr/bin/env python

'''wikitext.py : gather wikipedia texts associated with entities
'''

from mediawiki import MediaWiki, DisambiguationError
import numpy as np
import pandas as pd

ENT_CSV = '../data/190128-df-ent.csv'
OUT_CSV = "../data/wikitext-for-ents.csv"
# wikipedia api asks for a custom user agent
USER_AGENT = 'histmarkTool/0.1 run by abirdsall'

def make_mediawiki(user_agent=USER_AGENT):
    # by default uses english wikipedia
    wikipedia = MediaWiki(user_agent=user_agent)
    return wikipedia

def read_df_ent(csv_path=ENT_CSV):
    df_ent = pd.read_csv(ENT_CSV) #.drop("Unnamed: 0", axis=1)
    return df_ent

def filter_ents(df_ent):
    # only ents that are in at least two different markers
    mrkrs_per_ent = df_ent.groupby('text').marker_id.apply(lambda x: len(x.unique()))
    ents_to_keep = mrkrs_per_ent[mrkrs_per_ent>1].index.values
    df_ent = df_ent[df_ent.text.isin(ents_to_keep)]
    return df_ent

def get_wikitext(df_ent, wikipedia, out_csv_path=OUT_CSV):
    df_empty = pd.DataFrame(columns=['entity','label','pageid','title','cats','links','summarize','content'])
    df_empty.to_csv(out_csv_path, index=False)

    # initialize lists that will be columns in dataframe
    ents = []
    labels = []
    titles = []
    pageids = []
    contents = []
    summaries = []
    links = []
    categories = []

    # skipping: html (would rather not), backlinks (slow), infobox (not in package)

    ent_tuples = text_label.unique()
    for i, (ent_text, ent_label) in enumerate(ent_tuples):
        try:
            search_results = wikipedia.search(ent_text)
            if len(search_results)>0:
                top_search_result = search_results[0]
                p = wikipedia.page(top_search_result)
            else:
                p = None
                print("no search results for {}. skipping".format(ent_text))
                continue
        except DisambiguationError as d:
            # if possible, on disamb page take first suggestion that mentions Washington DC
            remove_punc = lambda string: ''.join(e for e in string if (e.isalnum() or e==' ' or e=='-'))
            # look for washington dc in d.details['description'], which has more text than d.options
            cleaned_descriptions = np.array([remove_punc(x['description']).lower() for x in d.details])
            has_dc = np.where([('washington dc' in cd) for cd in cleaned_descriptions])[0]
            if len(has_dc)>0:
                # get actual wikipedia page title to directly navigate to using d.options
                dc_page = d.options[has_dc[0]]
                print('hit disamb page for {}, using result {}'.format(ent_text, dc_page))
                p = wikipedia.page(dc_page)
            # otherwise skip
            else:
                print('hit disamb page for {}, couldn\'t find result. skipping.'.format(ent_text))
        # don't let other random hiccups stop the process
        except Exception as e:
            print("unexpected exception for {}: {}. skipping.".format(ent_text, e))
        else:
            ents.append(ent_text)
            labels.append(ent_label)
            titles.append(p.title)
            pageids.append(p.pageid)
            contents.append(p.content)
            summaries.append(p.summarize())
            links.append(p.links)
            categories.append(p.categories)
            # every 100th time or at end of loop,
            # append to CSV
            if (i%100==0) or (i==ent_tuples.shape[0]-1):
                print("{} / {}. appending to {}".format(i+1, ent_tuples.shape[0], out_csv_path))
                df = pd.DataFrame({'entity': ents,
                                   'label': labels,
                                   'pageid': pageids,
                                   'title': titles,
                                   'cats': categories,
                                   'links': links,
                                   'summarize': summaries,
                                   'content': contents})
                print("adding df with head {}".format(df.head()))
                with open(out_csv_path, 'a') as f:
                    df.to_csv(f, header=False, index=False)
                if (i==ent_tuples.shape[0]-1):
                    print('end of loop')
                # empty out lists
                ents = []
                labels = []
                titles = []
                pageids = []
                contents = []
                summaries = []
                links = []
                categories = []
    return None

if __name__ == '__main__':
    print('running wikitext.py from command line')
    wikipedia = make_mediawiki(USER_AGENT)
    print('wikitext.py: input entities {}'.format(ENT_CSV))
    df_ent = read_df_ent(ENT_CSV)
    df_ent = filter_ents(df_ent)
    print('starting get_wikitext() to query wikipedia')
    print('output to {}'.format(OUT_CSV))
    get_wikitext(df_ent, wikipedia, OUT_CSV)
    print('wikitext.py: done.')
