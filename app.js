
let viz;
let refreshInterval;

const containerDiv = document.getElementById("vizContainer");
const url = "https://prod-apsoutheast-a.online.tableau.com/t/priyagunda/views/Project-TrafficCongestionatIntersections/Dashboard1";
const options = {
    hideTabs: true,
    height: window.innerHeight,
    width: window.innerWidth,
    onFirstInteractive: function() {
        console.log("Hey, my dashboard is interactive!");
    },
    onFirstVizSizeKnown: function() {
        console.log("Hey, my dashboard has a size!");
    }
}

function initViz() {
    viz = new tableau.Viz(containerDiv, url, options);
}

window.setInterval(() => {
    console.log("Refreshing...");
    viz.refreshDataAsync();
}, 30000);

// function refreshDataSource() {
//     console.log("Going to start refreshing..");
//     refreshInterval = window.setInterval(() => {
//         console.log("Refreshing...");
//         viz.refreshDataAsync();
//     }, 45000);
// }
// function stopRefresh(){
//     console.log("Stop the refresh!");
//     clearInterval(refreshInterval);
// }
// document.getElementById("start").addEventListener('click', refreshDataSource)
// document.getElementById("stop").addEventListener('click', stopRefresh)
initViz();