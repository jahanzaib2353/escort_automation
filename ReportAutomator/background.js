chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'SOLVE_CAPTCHA') {
    const { imageUrl, apiKey } = request;
    
    fetch(imageUrl)
      .then(res => res.blob())
      .then(blob => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      }))
      .then(base64 => {
        const formData = new URLSearchParams();
        formData.append('key', apiKey);
        formData.append('method', 'base64');
        formData.append('body', base64);
        formData.append('json', '1');

        return fetch('https://2captcha.com/in.php', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData.toString()
        }).then(res => res.json());
      })
      .then(data => {
        if (data && data.status === 1) {
          pollForResult(data.request, apiKey, sendResponse);
        } else {
          sendResponse({ success: false, error: data ? data.request : 'Unknown API error' });
        }
      })
      .catch(err => {
        console.error('Background error:', err);
        sendResponse({ success: false, error: err.message });
      });

    return true; 
  }
});

function pollForResult(id, apiKey, sendResponse) {
  let attempts = 0;
  const poll = setInterval(() => {
    attempts++;
    if (attempts > 24) {
      clearInterval(poll);
      sendResponse({ success: false, error: 'Timeout' });
      return;
    }

    fetch(`https://2captcha.com/res.php?key=${apiKey}&action=get&id=${id}&json=1`)
      .then(res => res.json())
      .then(data => {
        if (data && data.status === 1) {
          clearInterval(poll);
          sendResponse({ success: true, solution: data.request });
        } else if (data && data.request !== 'CAPCHA_NOT_READY') {
          clearInterval(poll);
          sendResponse({ success: false, error: data.request });
        }
      })
      .catch(err => console.error('Poll error:', err));
  }, 5000);
}