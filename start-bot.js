const { exec } = require("child_process");

// Menjalankan bot Python
const process = exec("python3 bot-trading.py", {detached:true, stdio:"ignore"});

process.unref();

process.stdout.on("data", (data) => {
  console.log(`stdout: ${data}`);
});

process.stderr.on("data", (data) => {
  console.error(`stderr: ${data}`);
});

process.on("close", (code) => {
  console.log(`Bot exited with code ${code}`);
});