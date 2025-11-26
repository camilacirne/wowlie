const { app, BrowserWindow, Menu } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const findFreePort = require('find-free-port');

let mainWindow;
let streamlitProcess;
let streamlitPort;

// Determinar se está em modo desenvolvimento ou produção
const isDev = !app.isPackaged;

// Configurar caminhos
const getAppPath = () => {
  if (isDev) {
    return __dirname;
  }
  return path.join(process.resourcesPath, 'app');
};

// Encontrar Python
const getPythonCommand = () => {
  // Em desenvolvimento, usar venv se existir
  if (isDev) {
    const venvPython = path.join(__dirname, 'venv', 'bin', 'python3');
    const fs = require('fs');
    if (fs.existsSync(venvPython)) {
      return venvPython;
    }
  }
  
  // Usar Python do sistema (PATH)
  if (process.platform === 'win32') {
    return 'python';
  }
  return 'python3';
};

// Iniciar servidor Streamlit
async function startStreamlit() {
  return new Promise((resolve, reject) => {
    // Encontrar porta livre
    findFreePort(8501, (err, freePort) => {
      if (err) {
        reject(err);
        return;
      }

      streamlitPort = freePort;
      const appPath = getAppPath();
      const pythonCmd = getPythonCommand();
      const streamlitApp = path.join(appPath, 'streamlit_app.py');

      console.log('📂 App Path:', appPath);
      console.log('🐍 Python:', pythonCmd);
      console.log('📄 Streamlit App:', streamlitApp);
      console.log('🔌 Port:', streamlitPort);

      // Argumentos do Streamlit
      const args = [
        '-m', 'streamlit', 'run',
        streamlitApp,
        `--server.port=${streamlitPort}`,
        '--server.headless=true',
        '--browser.gatherUsageStats=false',
        '--server.address=localhost'
      ];

      // Iniciar processo
      streamlitProcess = spawn(pythonCmd, args, {
        cwd: appPath,
        env: { ...process.env }
      });

      streamlitProcess.stdout.on('data', (data) => {
        console.log(`Streamlit: ${data}`);
      });

      streamlitProcess.stderr.on('data', (data) => {
        console.error(`Streamlit Error: ${data}`);
      });

      streamlitProcess.on('error', (error) => {
        console.error('Erro ao iniciar Streamlit:', error);
        console.error('Certifique-se que Python está instalado e no PATH');
        console.error('Execute: pip install -r requirements.txt');
        
        // Mostrar mensagem de erro ao usuário
        const { dialog } = require('electron');
        dialog.showErrorBox(
          'Erro ao iniciar',
          'Não foi possível iniciar o servidor Streamlit.\n\n' +
          'Certifique-se que:\n' +
          '1. Python está instalado\n' +
          '2. As dependências estão instaladas (pip install -r requirements.txt)\n' +
          '3. Streamlit está instalado (pip install streamlit)\n\n' +
          `Erro: ${error.message}`
        );
        reject(error);
      });

      // Aguardar servidor iniciar
      setTimeout(() => {
        resolve(`http://localhost:${streamlitPort}`);
      }, 3000);
    });
  });
}

// Criar janela principal
function createWindow(url) {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      devTools: isDev
    },
    autoHideMenuBar: !isDev,
    title: 'WowLie Wallet'
  });

  // Remover menu em produção
  if (!isDev) {
    Menu.setApplicationMenu(null);
  }

  // Carregar aplicação
  mainWindow.loadURL(url);

  // Abrir DevTools apenas em desenvolvimento
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Prevenir navegação externa
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith(`http://localhost:${streamlitPort}`)) {
      event.preventDefault();
      require('electron').shell.openExternal(url);
    }
  });
}

// Quando o Electron estiver pronto
app.whenReady().then(async () => {
  try {
    console.log('🚀 Iniciando WowLie Wallet...');
    const url = await startStreamlit();
    console.log('✅ Streamlit iniciado:', url);
    createWindow(url);
  } catch (error) {
    console.error('❌ Erro ao iniciar:', error);
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(`http://localhost:${streamlitPort}`);
    }
  });
});

// Encerrar Streamlit ao fechar
app.on('window-all-closed', () => {
  if (streamlitProcess) {
    streamlitProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (streamlitProcess) {
    streamlitProcess.kill();
  }
});
