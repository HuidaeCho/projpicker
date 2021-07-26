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
    let data = geomsLayer.toGeoJSON()
    let logicalOp = document.querySelector(
                        'input[name="logical_op"]:checked').value
    data.logicalOperator = logicalOp
    ajaxRequest('/query', JSON.stringify(data), xhr => {
        queryResults = JSON.parse(xhr.response);
        populateCRSList(Object.keys(queryResults));
    });
};

function populateCRSList(crsIds) {
    let crsList = document.getElementById('crs-list');
    removeAllChildNodes(crsList);

    crsIds.forEach(crsId => {
        let crsName = queryResults[crsId].crs_name;

        let li = document.createElement('li');
        li.appendChild(document.createTextNode(crsName + ' '));

        let span = document.createElement('span');
        span.appendChild(document.createTextNode(`(${crsId})`));
        span.classList.add('crs-id');
        li.appendChild(span);

        li.onclick = () => {
            selectCRS(crsId);
        };
        crsList.appendChild(li);
    });
}

function selectCRS(crsId) {
    let crs = queryResults[crsId];

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

    let s = crs.south_lat
    let n = crs.north_lat
    let w = crs.west_lon
    let e = crs.east_lon
    let coors = [[[w, n], [e, n], [e, s], [w, s]]]

    drawCRSBBox(coors)
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

let queryResults = null;

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
