// 1. Check if we are supposed to be looping on page load
chrome.storage.local.get(['isLooping', 'apiKey', 'email', 'messages', 'targetUrl'], async (data) => {
  if (data.isLooping && data.apiKey && data.email) {
    // Check if we're on the 502 error page
    const error502Img = document.querySelector('img[src*="/static/img/502.png"]');
    if (error502Img) {
      console.log('⚠️ 502 Error detected. Clicking TAP HERE...');
      showStatus('⚠️ 502 Error. Redirecting...', '#ffc107');
      
      const tapHereBtn = document.querySelector('a.alertError');
      if (tapHereBtn) {
        tapHereBtn.click();
        setTimeout(() => {
          if (data.targetUrl) {
            window.location.href = data.targetUrl;
          } else {
            window.location.href = '/';
          }
        }, 1000);
      }
      return;
    }

    // Only run automation if we are on the correct target URL
    if (window.location.href.includes(data.targetUrl)) {
      console.log('✅ Loop mode active. Starting automation...');
      
      const randomMsg = data.messages && data.messages.length > 0 
        ? data.messages[Math.floor(Math.random() * data.messages.length)] 
        : "Suspicious activity reported.";
      
      // DEAD TARGET DETECTION
      if (!document.querySelector('#reportButton') || document.body.innerText.includes('404') || document.body.innerText.includes('Not Found')) {
        showStatus('🛑 TARGET DIED. Loop stopped.', 'red');
        chrome.runtime.sendMessage({ action: 'TARGET_DEAD' }).catch(() => {});
        await chrome.storage.local.set({ isLooping: false });
        return;
      }

      await runAutomation(data.apiKey, data.email, randomMsg);
    }
  }
});

function showStatus(message, color = '#28a745') {
  let statusDiv = document.getElementById('automator-status');
  if (!statusDiv) {
    statusDiv = document.createElement('div');
    statusDiv.id = 'automator-status';
    statusDiv.style.cssText = `
      position: fixed; top: 10px; right: 10px;
      background: ${color}; color: white;
      padding: 10px 15px; border-radius: 5px;
      font-family: Arial, sans-serif; font-size: 14px; font-weight: bold;
      z-index: 999999; box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    `;
    document.body.appendChild(statusDiv);
  }
  statusDiv.textContent = message;
  statusDiv.style.background = color;
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

function waitForElement(selector, timeout = 10000) {
  return new Promise(resolve => {
    const start = Date.now();
    const check = () => {
      const el = document.querySelector(selector);
      if (el && el.offsetParent !== null) {
        resolve(el);
      } else if (Date.now() - start > timeout) {
        resolve(null);
      } else {
        setTimeout(check, 200);
      }
    };
    check();
  });
}

async function simulateTyping(element, text) {
  element.focus();
  element.value = '';
  for (const char of text) {
    element.value += char;
    element.dispatchEvent(new KeyboardEvent('keydown', { key: char, bubbles: true }));
    element.dispatchEvent(new KeyboardEvent('keypress', { key: char, bubbles: true }));
    element.dispatchEvent(new InputEvent('input', { bubbles: true }));
    await sleep(30);
  }
  element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
  element.dispatchEvent(new Event('change', { bubbles: true }));
  element.blur();
}

async function runAutomation(apiKey, email, customMessage) {
  try {
    showStatus('⏳ Clicking Report Button...', '#17a2b8');
    const reportBtn = await waitForElement('#reportButton');
    if (reportBtn) {
      reportBtn.click();
    } else {
      showStatus('❌ Report button not found!', '#dc3545');
      chrome.runtime.sendMessage({ action: 'AUTOMATION_FINISHED' }).catch(() => {});
      return;
    }

    showStatus('⏳ Waiting for modal...', '#17a2b8');
    const modal = await waitForElement('.report-modal');
    if (!modal) {
      showStatus(' Modal did not appear!', '#dc3545');
      chrome.runtime.sendMessage({ action: 'AUTOMATION_FINISHED' }).catch(() => {});
      return;
    }
    await sleep(1000);

    showStatus('⏳ Selecting Scam Report...', '#17a2b8');
    const scamRadio = await waitForElement('input[value="SCAM"]');
    if (scamRadio) {
      const label = scamRadio.closest('label') || scamRadio.parentElement;
      label.click();
      await sleep(200);
      scamRadio.checked = true;
      scamRadio.dispatchEvent(new Event('change', { bubbles: true }));
    }
    await sleep(500);

    showStatus('⏳ Filling details...', '#17a2b8');
    const detailsInput = await waitForElement('textarea#reportPostDetails');
    if (detailsInput) {
      await simulateTyping(detailsInput, customMessage);
    } else {
      showStatus('❌ Details field not found!', '#dc3545');
      chrome.runtime.sendMessage({ action: 'AUTOMATION_FINISHED' }).catch(() => {});
      return;
    }
    await sleep(500);

    showStatus('⏳ Filling email...', '#17a2b8');
    const emailInput = await waitForElement('input#postReportEmailConfirmation');
    if (emailInput) {
      await simulateTyping(emailInput, email);
    } else {
      showStatus('❌ Email field not found!', '#dc3545');
      chrome.runtime.sendMessage({ action: 'AUTOMATION_FINISHED' }).catch(() => {});
      return;
    }
    await sleep(500);

    showStatus('⏳ Solving Captcha...', '#17a2b8');
    const captchaSolved = await solveCaptcha(apiKey);
    if (!captchaSolved) {
      showStatus('❌ Captcha failed!', '#dc3545');
      chrome.runtime.sendMessage({ action: 'AUTOMATION_FINISHED' }).catch(() => {});
      return;
    }
    await sleep(1000);

    showStatus('⏳ Submitting Report...', '#17a2b8');
    const submitBtn = await waitForElement('input#postReportButtonSend, .button-wrapper input[type="submit"]');
    if (submitBtn) {
      submitBtn.click();
    } else {
      showStatus('❌ Submit button not found!', '#dc3545');
      chrome.runtime.sendMessage({ action: 'AUTOMATION_FINISHED' }).catch(() => {});
      return;
    }

    showStatus('⏳ Handling Security Check...', '#17a2b8');
    await handleCloudflare();
    
    // CHECK FOR 502 ERROR AFTER CLOUDFLARE
    await sleep(2000);
    const error502Img = document.querySelector('img[src*="/static/img/502.png"]');
    if (error502Img) {
      console.log('⚠️ 502 Error detected after submit. Clicking TAP HERE...');
      showStatus('⚠️ 502 Error. Redirecting...', '#ffc107');
      
      const tapHereBtn = document.querySelector('a.alertError');
      if (tapHereBtn) {
        tapHereBtn.click();
        await sleep(1000);
        
        // Get target URL from storage and redirect
        chrome.storage.local.get('targetUrl', (data) => {
          if (data.targetUrl) {
            window.location.href = data.targetUrl;
          } else {
            window.location.href = '/';
          }
        });
        return;
      }
    }
    
    showStatus('✅ Report Completed! Waiting for next loop...', '#28a745');
    chrome.runtime.sendMessage({ action: 'AUTOMATION_FINISHED' }).catch(() => {});

  } catch (error) {
    console.error('❌ Automation crashed:', error);
    showStatus('❌ Automation crashed. Check Console (F12).', '#dc3545');
    chrome.runtime.sendMessage({ action: 'AUTOMATION_FINISHED' }).catch(() => {});
  }
}

function solveCaptcha(apiKey) {
  return new Promise((resolve) => {
    let attempts = 0;
    const checkImg = setInterval(() => {
      attempts++;
      if (attempts > 120) {
        clearInterval(checkImg);
        resolve(false);
        return;
      }

      const img = document.getElementById('captcha_image_itself') || document.querySelector('img[src*="captcha.drome6.com/captchas/"]');
      if (img && img.src) {
        clearInterval(checkImg);
        chrome.runtime.sendMessage(
          { action: 'SOLVE_CAPTCHA', imageUrl: img.src, apiKey },
          (response) => {
            if (response && response.success) {
              const input = document.querySelector('#captcha_code') || document.querySelector('input[name="captchaCode"]');
              if (input) {
                simulateTyping(input, response.solution).then(() => {
                  input.style.border = "3px solid #00FF00";
                  resolve(true);
                });
              } else {
                resolve(false);
              }
            } else {
              resolve(false);
            }
          }
        );
      }
    }, 1000);
  });
}

async function handleCloudflare() {
  return new Promise((resolve) => {
    let resolved = false;
    const cfObserver = new MutationObserver(async (mutations, obs) => {
      const cfText = document.querySelector('p[id="zezB9"]');
      if (cfText && cfText.innerText.includes('security service') && !resolved) {
        resolved = true;
        for (let i = 0; i < 5; i++) {
          document.dispatchEvent(new MouseEvent('mousemove', {
            view: window, bubbles: true, cancelable: true,
            clientX: Math.random() * window.innerWidth,
            clientY: Math.random() * window.innerHeight
          }));
          await sleep(500);
        }
        const iframe = document.querySelector('iframe[src*="challenges.cloudflare.com"]');
        if (iframe) {
          try {
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            const checkbox = iframeDoc.querySelector('input[type="checkbox"]') || iframeDoc.querySelector('.cb-lb');
            if (checkbox) checkbox.click();
          } catch (e) {
            iframe.click();
            if (iframe.parentElement) iframe.parentElement.click();
          }
        }
        const waitObserver = new MutationObserver((m, o) => {
          const successText = document.querySelector('h2[id="Yvat5"]'); 
          const isGone = !document.querySelector('p[id="zezB9"]');
          if (successText || isGone) {
            o.disconnect();
            obs.disconnect();
            resolve(true);
          }
        });
        waitObserver.observe(document.body, { childList: true, subtree: true });
      }
    });
    cfObserver.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => {
      if (!resolved) {
        cfObserver.disconnect();
        resolve(false);
      }
    }, 60000);
  });
}