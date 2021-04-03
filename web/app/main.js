// set up leaflet map
var dc_center = [38.8977, -77.033];
var map = L.map('map').setView(dc_center, 14);

var layer = L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'
});

map.addLayer(layer);

// use mouse click on map to id user location
var popup = L.marker(dc_center).addTo(map);
function onMapClick(e) {
    popup
        .setLatLng(e.latlng)
        .addTo(map);
    document.getElementById('latInput').value = e.latlng.lat;
    document.getElementById('lonInput').value = e.latlng.lng;
}
map.on('click', onMapClick);

// generic ajax post request with json returned datatype
makePostCall = function (url, data) {
    var json_data = JSON.stringify(data);

    return $.ajax({
      type: "POST",
      url: url,
      data: json_data,
      dataType: "json",
      contentType: "application/json;charset=utf-8",
    });
  }

drawMarkersMap = function (markers) {
    // custom icon style requires mucking around with html, see
    // https://stackoverflow.com/a/40870439
    const myCustomColor = 'orange'
    const markerHtmlStyles = `
      background-color: ${myCustomColor};
      width: 3rem;
      height: 3rem;
      display: block;
      left: -1.5rem;
      top: -1.5rem;
      position: relative;
      border-radius: 3rem 3rem 0;
      transform: rotate(45deg);
      border: 1px solid #FFFFFF`
    const icon = L.divIcon({
      className: "my-custom-pin",
      iconAnchor: [0, 24],
      labelAnchor: [-6, 0],
      popupAnchor: [0, -36],
      html: `<span style="${markerHtmlStyles}" />`
    })

    var allMarkers = L.featureGroup();
    var i;
    for (i = 0; i < markers.length; i++) {
        var marker = L.marker([markers[i]['lat'], markers[i]['lon']],
            {icon: icon})
            .bindPopup(markers[i]['title']);
        marker.addTo(allMarkers);
    }
    // add markers to existing map
    allMarkers.addTo(map);

    map.fitBounds(allMarkers.getBounds());
}


// and here a call example
$("#inputForm").submit(function(e) {

    e.preventDefault(); // do not execute the actual submit of the form

    var form = $(this);
    var formdata = form.serializeArray();
    console.log(formdata);
    var data = {};
    data["cluster"] = []
    // convert name, value structure into expected json
    $(formdata ).each(function(index, obj){
        if (obj.name == "cluster") {
          // combine cluster checkboxes into single list
          data["cluster"].push(obj.value);
        } else {
        // all others use name: value
          data[obj.name] = obj.value;
        }
    });
    // todo fix hard-coded url to call
    var url = form.attr('action');
    makePostCall(url, data)
      .done(function( data, textStatus, jqXHR ){
          console.log("made call! status:", textStatus);
          drawMarkersMap(data["markers"]);
          $("#stepone").addClass("inactive");
          $("#steptwo").removeClass("inactive");
          listMarkersTable(data["markers"]);
      })
      .fail(function( jqXHR, textStatus, errorThrown ){
             console.log("makepostcall failed:");
             console.log(textStatus);
             console.log(errorThrown);
             alert("Sorry, something went wrong!");
      });
});
// submit form choosing starting point
$("#chooseStart").submit(function(e) {

    e.preventDefault(); // do not execute the actual submit of the form

    var form = $(this);
    var formdata = form.serializeArray();
    console.log(formdata);
    var data = {};
    // convert name, value structure into expected json of start_marker and
    // radius
    $(formdata ).each(function(index, obj){
         data[obj.name] = obj.value;
    });
    // todo fix hard-coded url to call
    var url = form.attr('action');
    makePostCall(url, data)
      .done(function( data, textStatus, jqXHR ){
          console.log("made call! status:", textStatus);
          console.log(data);
          showRouteMap(data["markers"], data["route_polylines"]);
          $("#steptwo").addClass("inactive");
          $("#stepthree").removeClass("inactive");
          showRouteTable(data["markers"]);
          console.log(data["route_str"]);
          console.log(data["optimal_duration"]);
          $("#routeOverview").html("<b>Route overview:</b> " + data["route_str"]);
          $("#routeDuration").html("<b>Optimized route duration:</b> " + data["optimal_duration"]);
      })
      .fail(function( jqXHR, textStatus, errorThrown ){
             console.log("makepostcall failed:");
             console.log(textStatus);
             console.log(errorThrown);
             alert("Sorry, something went wrong!");
      });
});

function listMarkersTable(markers) {
    // construct string of new rows
    var i;
    var newRows = "";
    for (i = 0; i < markers.length; i++) {
        var currentMarker = markers[i];
        var newRow = `
            <tr>
                <td>
                 <div class="radio">
                     <input type="radio" name='start_marker' value=${currentMarker.marker_id} id=${currentMarker.marker_id}/>
                     <label for=${currentMarker.marker_id}>Choose this</label>
                 </div>
                </td>
                <td><a href="${currentMarker.url}">
                        ${currentMarker.title}
                    </a>
                </td>
                <td>${currentMarker.text_clean.slice(0, 280)}...</td>
                <td><img src="${currentMarker.img_src}" width=200px /></td>
            </tr>
            `;
        newRows += newRow;
    }
    $('#markersTable').append(newRows);
}

function showRouteMap(markers, route_polylines) {
    var i;
    for (i = 0; i < markers.length; i++) {
        var currentMarker = markers[i];
        var marker = L.marker([currentMarker.lat, currentMarker.lon]).addTo(map)
            .bindPopup(currentMarker.title);
    }
    var polyline = L.polyline(route_polylines, {color: 'red'}).addTo(map);
    map.fitBounds(polyline.getBounds());
}

function showRouteTable(markers) {
    // construct string of new rows
    var i;
    var newRows = "";
    for (i = 0; i < markers.length; i++) {
        var currentMarker = markers[i];
        var newRow = `
            <tr>
                <td>${i+1}</td>
                <td><a href="${currentMarker.url}">
                        ${currentMarker.title}
                    </a>
                <td>
                <td>${currentMarker.text_clean.slice(0, 280)}...</td>
                <td><img src="${currentMarker.img_src}" width=200px /></td>
                <td>${currentMarker.marker_ents}</td>
            </tr>
            `;
        newRows += newRow;
    }
    $('#routeTable').append(newRows);
}

function validateForm() {
    console.log("running validateForm()");
    var lat = document.forms["inputForm"]["lat"].value;
    var lon = document.forms["inputForm"]["lon"].value;
    if ((lat == "")||(lon == "")) {
        alert("Coordinates must be provided; click on map to set");
        return false;
    }
    var checkboxes = document.forms["inputForm"].elements["cluster"];
    //console.log(checkboxes);
    var numChecked = 0;
    for (var i=0, len=checkboxes.length; i<len; i++) {
        numChecked = numChecked + checkboxes[i].checked;
    }
    console.log("numChecked:");
    console.log(numChecked);
    if (numChecked<1) {
        alert("At least one checkbox must be selected");
        return false;
    }
} 
