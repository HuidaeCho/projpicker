// vim: set tabstop=4 shiftwidth=4 expandtab:

var map = L.map(
    'map', {
        center: [34.2347566, -83.8676613],
        crs: L.CRS.EPSG3857,
        zoom: 5,
        zoomControl: true,
        preferCanvas: false,
    }
);

var tileLayer = L.tileLayer(
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

// FeatureGroup is to store editable layers.
var geomsLayer = new L.geoJSON().addTo(map);

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

map.on(L.Draw.Event.CREATED, function (e) {
    geomsLayer.addLayer(e.layer);
    sendQuery();
});

function populateCRSList(crsKeys) {
    const list = document.getElementById('crs-list');
    while (list.firstChild) {
        list.removeChild(list.firstChild);
    }
    const listItems = crsKeys.map( function(element) {
            return `<li tabindex='1' id='${element}' onclick='onCRSSelect()'>${element}</li>` });

    list.innerHTML = listItems.join('');
}

function onCRSSelect() {
    var selectedId = document.activeElement.id;
    selectedCRS = queryResults[selectedId];

    var s = selectedCRS.south_lat
    var n = selectedCRS.north_lat
    var w = selectedCRS.west_lon
    var e = selectedCRS.east_lon

    var coors = [[[w, n], [e, n], [e, s], [w, s]]]

    var crsInfo = document.getElementById('crs-info')
    var crsInfoList = [];
        crsInfoList.push(`<tr><td>Name</td><td>Value</td></tr>`)
    crsInfoList.push(`<tr><td>CRS Authority: </td><td>${selectedCRS.crs_auth_name}</td></tr>`)
    crsInfoList.push(`<tr><td>CRS Code: </td><td>${selectedCRS.crs_code}</td></tr>`)
    crsInfoList.push(`<tr><td>CRS Type: </td><td>${selectedCRS.proj_table}</td></tr>`)
    crsInfoList.push(`<tr><td>Unit: </td><td>${selectedCRS.unit}</td></tr>`)
    crsInfoList.push(`<tr><td>South: </td><td>${selectedCRS.south_lat}</td></tr>`)
    crsInfoList.push(`<tr><td>North: </td><td>${selectedCRS.north_lat}</td></tr>`)
    crsInfoList.push(`<tr><td>West: </td><td>${selectedCRS.west_lon}</td></tr>`)
    crsInfoList.push(`<tr><td>East: </td><td>${selectedCRS.east_lon}</td></tr>`)
    crsInfoList.push(`<tr><td>Area: </td><td>${Math.round(selectedCRS.area_sqkm)}</td></tr>`)
    crsInfo.innerHTML = crsInfoList.join('');

    console.log(coors)

    drawCRSBBox(coors)

}


var queryResults = null;

// Use main logic function to query on events.
function sendQuery() {
    var data = geomsLayer.toGeoJSON()
    var logicalOp = document.querySelector('input[name="logical_op"]:checked').value
    data.logicalOperator = logicalOp
    ajaxRequest('/query', JSON.stringify(data), xhr => {
        queryResults = JSON.parse(xhr.response);
        populateCRSList(Object.keys(queryResults));
    });
};

function onClick(logicalOp) {
    sendQuery();
}

// Intial empty bbox geometry; Seperate layer group from geomsLayer so as to not
// interfere with ProjPicker query.
var bboxLayer = L.geoJSON(null, {
    style: {
        color: 'red',
        opacity: 0.3
    }
}).addTo(map);

function drawGeometries(geoms, push=false) {
    geomsLayer.clearLayers();
    geomsLayer.addData(geoms);
    map.fitBounds(geomsLayer.getBounds());
    if (push)
        pushGeometries();
}

function drawCRSBBox(geom) {
    bboxLayer.clearLayers();
    bboxLayer.addData({
        "type": "Polygon",
        "coordinates": geom
    });
    map.fitBounds(bboxLayer.getBounds());
}
