
const {app, BrowserWindow} = require('electron');

function ElectronMainMethod() {
    const launchWindow = new BrowserWindow({
        title: "Expense Tracker",
        width: 800,
        height: 600,
    });
    const appURL = "http://localhost:8000";
    launchWindow.loadURL(appURL);
}//end main()
app.whenReady().then(ElectronMainMethod)