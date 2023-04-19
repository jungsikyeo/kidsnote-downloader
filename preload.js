const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
    ipcRenderer: {
        send: (channel, data) => {
            ipcRenderer.send(channel, data);
        },
        invoke: (channel, data) => {
            return ipcRenderer.invoke(channel, data);
        },
        on(channel, callback) {
            ipcRenderer.on(channel, callback);
        },
    },
});
