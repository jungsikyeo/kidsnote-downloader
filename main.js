const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { exec } = require('child_process');
const path = require("path");
const { spawn } = require('child_process');

let mainWindow;
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1100,
        height: 700,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
        },
    });

    mainWindow.loadFile('index.html');
    // mainWindow.webContents.openDevTools();
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

ipcMain.handle('select-download-folder', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openDirectory'],
    });
    if (result.canceled) {
        return null;
    }
    return result.filePaths[0];
});

ipcMain.on('run-python-script', (event, command) => {
    const [...args] = command.split('|');
    let cmdPath;
    const appPath = app.isPackaged ? process.resourcesPath : path.join(app.getAppPath(), 'dist')
    if (process.platform === "win32") {
        cmdPath = path.join(appPath, 'main.exe');
    } else if (process.platform === "darwin") {
        cmdPath = path.join(appPath, 'main');
    } else {
        cmdPath = path.join(appPath, 'main');
    }

    const pythonProcess = spawn(cmdPath, args, { encoding: 'utf-8' });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Stdout: ${data}`);
        try {
            const message = JSON.parse(data.toString('utf-8'));
            if (message.type === 'log') {
                event.sender.send('log-message', message.message);
            } else if (message.type === 'download-complete') {
                event.sender.send('download-complete', true);
            }
        } catch (error) {
            console.error(`JSON parsing error: ${error.message}`);
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            console.error(`Python script exited with code: ${code}`);
            event.sender.send('download-complete', false);
        }
    });
});