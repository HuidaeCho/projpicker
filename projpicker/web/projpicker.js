// vim: set tabstop=4 shiftwidth=4 expandtab:

/********** FUNCTIONS **********/

// http://developer.mozilla.org/en/docs/AJAX:Getting_Started
function ajaxRequest(url, data, func, mimeType) {
    let xhr = null;

    // create an XMLHTTP instance
    if (window.XMLHttpRequest) { // Mozilla, Safari, ...
        xhr = new XMLHttpRequest();
        if (xhr.overrideMimeType)
            // some web servers return a non-standard mime type
            xhr.overrideMimeType(mimeType || 'text/html');
    } else if (window.ActiveXObject) { // IE
        try {
            xhr = new ActiveXObject('Msxml2.XMLHTTP');
        }
        catch (e) {
            try {
                xhr = new ActiveXObject('Microsoft.XMLHTTP');
            }
            catch (e) { }
        }
    }
    if (!xhr) {
        alert('Cannot create an XMLHTTP instance.');
        return;
    }

    // this function has no arguments
    xhr.onreadystatechange = () => {
        if (xhr.readyState != 4)
            return;
        if (func)
            func(xhr);
    }

    let method = data == null ? 'GET' : 'POST';

    // xhr.open(method, url, asynchronous)
    xhr.open(method, url, true);

    // xhr.send(POST data)
    // required even if the method is not POST
    xhr.send(data);
}

function removeAllChildNodes(element) {
    while (element.firstChild)
        element.removeChild(element.firstChild);
}

// Use main logic function to query on events.
function sendQuery() {
    let query = document.querySelector(
                    'input[name="logical_op"]:checked').value + '\n';
    let features = geomsLayer.toGeoJSON().features
    for (let i in features) {
        let geom = features[i].geometry;
        // Reverse coordinates as leaflet returns opposite order of what
        // ProjPicker takes
        if (geom.type == 'Point') {
            // Coordinates in "Point" type are single-depth tuple [i, j]
            let coor = geom.coordinates;
            let lat = coor[1];
            let lon = coor[0];
            query += `point ${lat},${lon}`;
        } else {
            // Coordinates in "Poly" type are in multi-depth array of size
            // [[[i0, j0], [i1, j1], ...]]; Move down array depth for easier
            // iteration
            query += 'poly';
            for (let j in geom.coordinates[0]) {
                let coor = geom.coordinates[0][j];
                let lat = coor[1];
                let lon = coor[0];
                query += ` ${lat},${lon}`;
            }
        }
        query += '\n';
    }
    ajaxRequest('query', query, xhr => {
        let queryResults = JSON.parse(xhr.response);
        populateCRSList(queryResults);
    });
};

function populateCRSList(queryResults) {
    let crsList = document.getElementById('crs-list');
    removeAllChildNodes(crsList);

    for (let i = 0; i < queryResults.length; i++) {
        let crs = queryResults[i];
        let li = document.createElement('li');
        li.appendChild(document.createTextNode(crs.crs_name + ' '));

        let crsId = `${crs.crs_auth_name}:${crs.crs_code}`;
        let span = document.createElement('span');
        span.appendChild(document.createTextNode(`(${crsId})`));
        span.classList.add('crs-id');
        li.appendChild(span);

        li.onclick = () => {
            selectCRS(crs);
        };
        crsList.appendChild(li);
    }
}

function selectCRS(crs) {
    let crsId = `${crs.crs_auth_name}:${crs.crs_code}`;
    let crsName = document.getElementById('crs-name');
    removeAllChildNodes(crsName);
    crsName.appendChild(document.createTextNode(crs.crs_name));

    let crsType = crs.proj_table.replace('_crs', '');
    crsType = crsType[0].toUpperCase() + crsType.substr(1);

    let crsItems = {
        'CRS ID': crsId,
        'CRS Type': crsType,
        'Unit': crs.unit,
        'South': crs.south_lat,
        'North': crs.north_lat,
        'West': crs.west_lon,
        'East': crs.east_lon,
        'Area': Math.round(crs.area_sqkm).toLocaleString()
    }

    let crsTable = document.getElementById('crs-table')
    removeAllChildNodes(crsTable);

    for (let key in crsItems) {
        let row = crsTable.insertRow();

        let cell = row.insertCell()
        cell.appendChild(document.createTextNode(key + ':'));

        cell = row.insertCell()
        cell.appendChild(document.createTextNode(crsItems[key]));

        if (['South', 'North', 'West', 'East'].indexOf(key) >= 0)
            cell.appendChild(document.createTextNode('\u00b0'));
        else if (key == 'Area') {
            cell.appendChild(document.createTextNode(' km'));
            let squared = document.createElement('sup');
            squared.appendChild(document.createTextNode('2'));
            cell.appendChild(squared);
        }
    }

    let s = crs.south_lat;
    let n = crs.north_lat;
    let w = crs.west_lon;
    let e = crs.east_lon;

    let coors;

    if (w > e) {
        coors = [[[w, n], [180, n], [180, s], [w, s]],
                 [[-180, n], [e, n], [e, s], [-180, s]]];
    } else
        coors = [[[w, n], [e, n], [e, s], [w, s]]];

    drawCRSBBox(coors);
}

function drawCRSBBox(geom) {
    bboxLayer.clearLayers();
    bboxLayer.addData({
        'type': 'Polygon',
        'coordinates': geom
    });
    map.fitBounds(bboxLayer.getBounds());
}

function drawGeometries(geoms) {
    geomsLayer.clearLayers();
    geomsLayer.addData(geoms);
    map.fitBounds(geomsLayer.getBounds());
}

/********** MAIN CODE **********/

let map = L.map(
    'map', {
        center: [0, 0],
        crs: L.CRS.EPSG3857,
        zoom: 2,
        zoomControl: true,
        preferCanvas: false,
    }
);

if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(position => {
        map.setView([position.coords.latitude, position.coords.longitude], 10);
    });
}

let tileLayer = L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        'attribution': 'Data by \u0026copy; \u003ca href="http://openstreetmap.org"\u003eOpenStreetMap\u003c/a\u003e, under \u003ca href="http://www.openstreetmap.org/copyright"\u003eODbL\u003c/a\u003e.',
        'detectRetina': false,
        'maxNativeZoom': 18,
        'maxZoom': 18,
        'minZoom': 0,
        'noWrap': true,
        'opacity': 1,
        'subdomains': 'abc',
        'tms': false
    }
).addTo(map);

// geomsLayers is to store editable layers.
let geomsLayer = new L.geoJSON().addTo(map);

new L.Control.Draw({
    position: 'topleft',
    draw: {
        'polyline': {
            'allowIntersection': false
        },
        circle: false,
        circlemarker: false,
        polyline: false
    },
    edit: {
        'poly': {
            'allowIntersection': false
        },
        'featureGroup': geomsLayer
    },
}).addTo(map);

map.on(L.Draw.Event.CREATED, e => {
    geomsLayer.addLayer(e.layer);
    sendQuery();
});

// Intial empty bbox geometry; Seperate layer group from geomsLayer so as
// to not interfere with ProjPicker query.
let bboxLayer = L.geoJSON(null, {
    style: {
        color: 'red',
        opacity: 0.3
    }
}).addTo(map);
