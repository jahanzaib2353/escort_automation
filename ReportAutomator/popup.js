document.addEventListener('DOMContentLoaded', async () => {
  const inputs = {
    targetUrl: document.getElementById('targetUrl'),
    apiKey: document.getElementById('apiKey'),
    email: document.getElementById('email'),
    messages: document.getElementById('messages')
  };
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const statusDiv = document.getElementById('status');

  const saved = await chrome.storage.local.get(Object.keys(inputs).concat('isLooping'));
  Object.keys(inputs).forEach(key => { if (saved[key]) inputs[key].value = saved[key]; });

  if (!inputs.messages.value) {
    inputs.messages.value = "Fake profile using stolen photos.\nSuspected scam, phone number does not match.\nDuplicate listing of another active profile.\nSuspicious activity, requesting immediate review.\nSpam content violating terms of service.";
  }

  if (saved.isLooping) {
    startBtn.style.display = 'none';
    stopBtn.style.display = 'block';
    statusDiv.textContent = '🟢 Looping active...';
    statusDiv.style.color = 'green';
  }

  startBtn.addEventListener('click', async () => {
    if (!inputs.targetUrl.value.trim() || !inputs.apiKey.value.trim() || !inputs.email.value.trim()) {
      statusDiv.textContent = '❌ URL, API Key, and Email required.';
      statusDiv.style.color = 'red';
      return;
    }

    const config = {
      targetUrl: inputs.targetUrl.value.trim(),
      apiKey: inputs.apiKey.value.trim(),
      email: inputs.email.value.trim(),
      messages: inputs.messages.value.split('\n').filter(m => m.trim() !== ''),
      isLooping: true
    };

    await chrome.storage.local.set(config);
    startBtn.style.display = 'none';
    stopBtn.style.display = 'block';
    statusDiv.textContent = '🚀 Navigating to target...';
    statusDiv.style.color = 'green';

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0] && tabs[0].id) {
        chrome.tabs.update(tabs[0].id, { url: config.targetUrl });
      }
    });
  });

  stopBtn.addEventListener('click', async () => {
    await chrome.storage.local.set({ isLooping: false });
    startBtn.style.display = 'block';
    stopBtn.style.display = 'none';
    statusDiv.textContent = '🛑 Loop stopped.';
    statusDiv.style.color = 'red';
  });

  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === 'STATUS_UPDATE') {
      statusDiv.textContent = message.text;
      statusDiv.style.color = message.color || '#333';
      if (message.text.includes('DEAD') || message.text.includes('Stopped')) {
        chrome.storage.local.set({ isLooping: false }).then(() => {
          startBtn.style.display = 'block';
          stopBtn.style.display = 'none';
        });
      }
    }
    
    if (message.action === 'AUTOMATION_FINISHED') {
      chrome.storage.local.get('isLooping', (data) => {
        if (data.isLooping) {
          statusDiv.textContent = '⏳ Waiting 15s before next loop...';
          statusDiv.style.color = '#17a2b8';
          setTimeout(() => {
             chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
               if (tabs[0] && tabs[0].id) {
                 chrome.tabs.reload(tabs[0].id); // Reload triggers content.js to run again
               }
             });
          }, 15000);
        }
      });
    }

    if (message.action === 'TARGET_DEAD') {
       chrome.storage.local.set({ isLooping: false });
       startBtn.style.display = 'block';
       stopBtn.style.display = 'none';
    }
  });
});