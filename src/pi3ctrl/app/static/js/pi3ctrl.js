/* global bootstrap: false */
let debug = window.location.hostname == '127.0.0.1'
let statusUpdater = null;


Date.prototype.addSecs = function(s) {

    this.setTime(this.getTime() + (s * 1000));
    return this;

}


function sleep(ms) {

    return new Promise(resolve => setTimeout(resolve, ms));

}


function getRelease() {

    url = "https://api.github.com/repos/psmsmets/pi3ctrl/releases"

    let promise1 = getResponse(url, 'GET');
    let promise2 = getResponse("/_version");

    // Resolve the promises
    Promise.all([promise1, promise2])
    .then(function(values) {
        let [ resp, version ] = values.map(x => JSON.parse(x.response));
        let current = resp.shift();

        // Compare current version vs latest GitHub release
        if(current.tag_name !== version.version) {
            console.log("A new version of Pi3Ctrl is available!");
        }

    }).catch(function(error) {
        console.log("Could not get releases! Not connected to the internet?");
    });
}


function validateForm(id, formCallBack) {

    var form = document.getElementById(id)

    form.addEventListener('submit', function (event) {

        event.preventDefault();
        event.stopPropagation();

        if (form.checkValidity()) {

            verifySecret()
            .then(secret => {
                if (secret === null) return
                formCallBack(form, secret)
            })
            form.querySelector('button[type=submit]').disabled = true

        }

        form.classList.add('was-validated')

    }, false)

    form.addEventListener('reset', function (event) {

        resetForm(form)

    }, false)

}


function resetForm(form) {

    form.reset()
    form.classList.remove('was-validated')
    form.querySelector('button[type=submit]').disabled = false;

}


function verifySecret() {

    var modal = new bootstrap.Modal(document.getElementById('secret-modal'), {
        backdrop: 'static',
        keyboard: false,
        focus: true,
    })

    return new Promise(resolve => {

        modal.show()

        var form = modal._element.getElementsByTagName('form')[0]
        var secret = null

        form.addEventListener('submit', function (event) {

            event.preventDefault();
            event.stopPropagation();

            if (form.checkValidity()) {

                secret = CryptoJS.SHA256(form.elements["inputSECRET"].value).toString()

                form.removeEventListener('submit', null);

                modal.hide()

            }

            form.classList.add('was-validated')

        }, false)

        modal._element.addEventListener('hidden.bs.modal', function (event) {

            form.reset()
            resolve(secret)

        })

    });

}


function add_ssid_psk(form, secret) {

    const ssid = form.elements["inputSSID"].value
    const psk = form.elements["inputPSK"].value

    getResponse("/_add_ssid_psk", { ssid: ssid, passphrase: psk, secret: secret }, 'POST')
    .then(resp => {

        if (resp.status !== 200) {

            alert("Error: " + resp.responseText)

        } else {

            alert("\"" + ssid + "\" added to the list of known wireless networks.")
            resetForm(form)

        }

    });

}


function autohotspot() {

    verifySecret().then(secret => {

        if (secret === null) return

        getResponse("/_autohotspot", { secret: secret }, 'POST')
        .then(resp => {

            if (resp.status !== 200) {

                alert("Error: " + resp.responseText)

            } else {

                alert("Wi-Fi autohotspot script triggered.\n\nConnection to the device could be lost.")

            }

        });

    })

}


function upload_soundfile(form, secret) {

    const files = document.getElementById("inputFile");
    const button = form.elements["inputButton"].value;

    const formData = new FormData(form);

    formData.append("file", files.files[0]);
    formData.append("button", button);
    formData.append("secret", secret);

    const requestOptions = {
        headers: {
            "Content-Type": files.files[0].contentType,
        },
        mode: "no-cors",
        method: "POST",
        files: files.files[0],
        body: formData,
    };

    fetch("_soundfile", requestOptions)
    .then((resp) => {
        if (resp.status !== 200) {
            (resp.text()).then(data => {
                alert("Error: " + data)
            });
        } else {
            alert('File uploaded!');
            resetForm(form)
        }
    });

}


function dataMetrics() {

    getResponse('/_metrics', {})
    .then(function(resp) {

        if (resp.status !== 200) return

        var dataset = JSON.parse(resp.responseText)

        // last
        var obj = dataset['last']
        var elem = document.querySelector('#metrics-last-button')
        elem.innerHTML = Object.keys(obj)[0]
        elem = document.querySelector('#metrics-last-timestamp')
        elem.innerHTML = obj[Object.keys(obj)[0]];

        // totals
        var metrics = document.querySelector('#metrics-total')
        var totals = dataset['total']
        Object.keys(totals).forEach(function(key) {
            metrics.innerHTML += ("<span class=\"badge text-bg-primary position-relative me-4\">" + key +
                                 "<span class=\"position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger\">" + totals[key] + "</span></span>");
        })

        // date series data
       const dateSeries = Object.keys(dataset.date).map(button => {
           const data = Object.entries(dataset.date[button]).map(([date, count]) => {
               const timestamp = new Date(date).getTime(); // Convert date to timestamp
               return [timestamp, count];
           });

           return {
               name: button,
               data: data.sort((a, b) => a[0] - b[0]) // Ensure data is sorted by date
           };
       });

       // date line chart
       Highcharts.chart('highcharts-date', {
           chart: {
               type: 'scatter'
           },
           title: {
               text: 'Button Activity Over Time'
           },
           xAxis: {
               type: 'datetime',
               title: {
                   text: 'Date'
               }
           },
           yAxis: {
               title: {
                   text: 'Count'
               }
           },
           plotOptions: {
               scatter: {
                   marker: {
                       radius: 5,  // Size of the points
                       symbol: 'circle'  // Shape of the points
                   },
                   lineWidth: 0  // Disable connecting lines
               }
           },
           series: dateSeries
       });

       // hour series data
       const hourSeries = Object.keys(dataset.hour).map(button => {
           const data = Array(24).fill(0);  // Initialize an array for 24 hours
  
           Object.entries(dataset.hour[button]).forEach(([hour, count]) => {
               data[parseInt(hour)] = count;  // Assign the count to the respective hour
           });

           return {
               name: button,
               data: data
           };
       });

       // hour column chart
       Highcharts.chart('highcharts-hour', {
           chart: {
               type: 'column'
           },
           title: {
               text: 'Button Activity by Hour of the Day'
           },
           xAxis: {
               categories: [...Array(24).keys()],  // Generates an array [0, 1, 2, ..., 23]
               title: {
                   text: 'Hour of the Day'
               }
           },
           yAxis: {
               title: {
                   text: 'Number of Triggers'
               },
               allowDecimals: false
           },
           series: hourSeries
       });

       // Map the weekday numbers to names
       const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

       // weekday series
       const weekdaySeries = Object.keys(dataset.weekday).map(button => {
           const data = Array(7).fill(0);  // Initialize an array for 7 days

           Object.entries(dataset.weekday[button]).forEach(([weekday, count]) => {
               data[parseInt(weekday)] = count;  // Assign the count to the respective weekday
           });

           return {
               name: button,
               data: data
           };
       });

       // weekday column chart
       Highcharts.chart('highcharts-weekday', {
           chart: {
               type: 'column'
           },
           title: {
               text: 'Button Activity by Day of the Week'
           },
           xAxis: {
               categories: weekdays,  // ["Sunday", "Monday", "Tuesday", ...]
               title: {
                   text: 'Day of the Week'
               }
           },
           yAxis: {
               title: {
                   text: 'Number of Triggers'
               },
               allowDecimals: false
           },
           series: weekdaySeries
});

    })

}


function updateStorage() {

    getResponse('/_storage')
    .then(function(resp) {

        let data = JSON.parse(resp.response)

        Highcharts.chart({
            chart: { height: 200, renderTo: 'highcharts-storage', type: 'bar', backgroundColor: 'none' },
            credits: { enabled: false },
            title: { text: 'Storage Space' },
            subtitle: { text: `(${(100 * data.free / data.total).toFixed(2)}% available out of a total of ${bytes(data.total, true)})` },
            tooltip: { formatter: function() { return bytes(this.y, true); } },
            xAxis: { visible: false },
            yAxis: { visible: false },
            exporting: { enabled: false },
            legend: { enabled: false },
            plotOptions: { series: { stacking: 'normal', dataLabels: { style: { fontSize: "14px" }, enabled: true, inside: true, formatter: function() { return bytes(this.y, true) } } } },
            series: [{ name: "Free", data: [data.free]}, { name: "Used", data: [data.used]}]
        });

    })

}


function statusUpdateLoop() {

    const progressbar = document.querySelector('#statusUpdater')
    if (progressbar === null) { return; }

    clearInterval(statusUpdater);
    let width = 0;

    statusUpdater = setInterval(progressBarWidth, 100);  // ms, times 100 gives 10s

    updateStorage()

    function progressBarWidth() {

        if (width == 100) {

            width = 0;
            statusUpdate()

        } else {

            width++;

        }

        progressbar.style.width = width + '%';
 
    }

}


function statusUpdate() {

    getResponse('/_systemd_status', { service: '*' })
    .then(function(resp) {

        if (resp.status !== 200) return

        var data = JSON.parse(resp.responseText)

        for (const [service, response] of Object.entries(data)) {

            var id = '#' + service.replace('.', '-')
            var obj_status = document.querySelector(id + '-status')
            var obj_response = document.querySelector(id + '-response > .accordion-body')

            if (response.returncode === null) continue

            if (response.returncode === 4) {

                obj_response.innerHTML = response.stderr
                obj_status.innerHTML = 'not found'

                if (!obj_status.classList.contains('bg-secondary')) {

                    obj_status.classList.remove('bg-success', 'bg-warning', 'bg-danger')
                    obj_status.classList.add('bg-secondary')

                }

                continue;

            }

            obj_response.innerHTML = response.stdout
            obj_status.innerHTML = response.status

            if (response.returncode === 0) {

                if (!obj_status.classList.contains('bg-success')) {

                    obj_status.classList.remove('bg-secondary', 'bg-warning', 'bg-danger')
                    obj_status.classList.add('bg-success')

                }

            } else if (response.status.includes('activating') || response.status.includes('inactive')) {

                if (!obj_status.classList.contains('bg-warning')) {

                    obj_status.classList.remove('bg-secondary', 'bg-success', 'bg-danger')
                    obj_status.classList.add('bg-warning')

                }

            } else {

                if (!obj_status.classList.contains('bg-danger')) {

                    obj_status.classList.remove('bg-secondary', 'bg-success', 'bg-warning')
                    obj_status.classList.add('bg-danger')

                }

            }

        }

    })

}


function bytes(bytes, label) {

    if (bytes == 0) return '';

    var s = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
    var e = Math.floor(Math.log(bytes)/Math.log(1024));
    var value = ((bytes/Math.pow(1024, Math.floor(e))).toFixed(2));

    e = (e<0) ? (-e) : e;

    if (label) value += ' ' + s[e];

    return value;

}


function loadConnectedSSID() {

    getResponse('/_ssid')
    .then(function(resp) {
        document.getElementById("ssid-connected").innerHTML = `Connected to <b>${JSON.parse(resp.response).ssid}</b>`
    });

}


function loadContent(nav) {

    // nav object set?
    if (nav === undefined) var nav = document.querySelector('#navbar > ul > li > a.active')

    // extract tab
    var tab = nav.getAttribute("data-bs-target")

    // get nav-content div
    var content = document.querySelector('#content');

    // clear content on load
    content.innerHTML = ''

    // stop status progressbar interval
    window.clearInterval(statusUpdater);

    // lazy load new content and trigger nav related functions
    getResponse("/_tab/" + tab)
    .then(function(resp) {

        if (resp.status !== 200) { console.log(resp); return; }
        content.innerHTML = JSON.parse(resp.responseText).html

    })
        .finally(function() {

            switch (tab) {

                case "ctrl":
                    validateForm('ctrl-upload', upload_soundfile)
                    break;

                case "data":
                    dataMetrics()
                    break;

                case "wifi":
		    loadConnectedSSID()
                    showPasswordToggle()
                    validateForm('wifi-add', add_ssid_psk)
                    break;

                case "status":
                    statusUpdate()
                    statusUpdateLoop()
                    break;

                default:
                    // do nothing

            }

            // activate tooltips
            var tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
            tooltips.forEach(function (tooltip) { new bootstrap.Tooltip(tooltip, { placement: 'bottom' }) })

        });

}


(function () {

    'use strict'

    loadContent();
    getRelease();

    var navbar = new bootstrap.Collapse(document.querySelector('#navbar'), {toggle: false})

    var navs = [].slice.call(document.querySelectorAll('#navbar > ul > li > a[data-bs-toggle="tab"]'))

    navs.forEach(function (nav) {

        nav.addEventListener('shown.bs.tab', function (event) {
            loadContent(nav);
            navbar.hide();
        })

    })

    // prevent page reload
    window.onbeforeunload = function(event) {

        //event.preventDefault();

    }

})()
