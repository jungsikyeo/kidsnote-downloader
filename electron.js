const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const url = require('url');
const { spawn } = require('child_process');
const isDev = require('electron-is-dev');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 680,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false,
    },
  });

  mainWindow.loadURL(
    url.format({
      pathname: path.join(__dirname, 'templates', 'index.html'),
      protocol: 'file:',
      slashes: true,
    })
  );

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  //mainWindow.webContents.openDevTools();
}

function runFlaskServer() {
  const flaskScriptPath = path.join(__dirname, 'app.py');
  const pythonExecutable = isDev ? 'python' : 'python3';

  const flaskProcess = spawn(pythonExecutable, [flaskScriptPath]);

  flaskProcess.stdout.on('data', (data) => {
    console.log(`Flask stdout: ${data}`);
  });

  flaskProcess.stderr.on('data', (data) => {
    console.error(`Flask stderr: ${data}`);
  });

  flaskProcess.on('close', (code) => {
    console.log(`Flask process exited with code ${code}`);
  });
}

app.on('ready', () => {
  runFlaskServer();
  createWindow();
});

ipcMain.handle('set-download-folder', async (event, data) => {
  console.log('Received data:', data);

  // Send data to Flask server
  try {
    const response = await fetch('http://127.0.0.1:5000/set-download-folder', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error while sending data to Flask server:', error);
    return { success: false };
  }
});


ipcMain.handle('start-download', async (event, data) => {
  // Call the /start-download endpoint of your Flask app and return the result
  try {
    const response = await fetch('http://127.0.0.1:5000/start-download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error while sending data to Flask server:', error);
    return { success: false };
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
