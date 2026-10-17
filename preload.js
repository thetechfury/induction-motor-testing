const { contextBridge, ipcRenderer } = require('electron');

// The page only gets one function: call(name, payload). Every operation is a named service in the main process.
contextBridge.exposeInMainWorld('bridge', {
  call: async (name, payload) => {
    const r = await ipcRenderer.invoke('api', name, payload);
    if (!r.ok) throw new Error(r.error);
    return r.data;
  },
});
