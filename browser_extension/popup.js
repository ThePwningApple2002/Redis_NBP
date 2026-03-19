document.getElementById('scrapeBtn').addEventListener('click', async () => {
    const btn = document.getElementById('scrapeBtn');
    const btnText = document.getElementById('btnText');
    const iconSend = document.getElementById('icon-send');
    const iconSpinner = document.getElementById('icon-spinner');
    const iconSuccess = document.getElementById('icon-success');
    const statusText = document.getElementById('statusText');
    
    btn.disabled = true;
    btnText.textContent = 'Salje se...';
    iconSend.classList.add('hidden');
    iconSpinner.style.display = 'block';
    statusText.className = 'status-text'; 
    statusText.textContent = '';
  
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      const executePromise = chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });
      
      const timeoutPromise = new Promise(resolve => setTimeout(resolve, 2000));
      
      await Promise.race([executePromise, timeoutPromise]);
  
      btnText.textContent = 'Poslato!';
      iconSpinner.style.display = 'none';
      iconSuccess.classList.remove('hidden');
  
      statusText.textContent = 'Recept poslat 😊';
      statusText.classList.add('show', 'text-success');
  
    } catch (err) {
      btnText.textContent = 'Nije poslato';
      iconSpinner.style.display = 'none';
      iconSend.classList.remove('hidden');
  
      statusText.textContent = 'Nesto je poslo po zlu.';
      statusText.classList.add('show', 'text-error');
      console.error("Scraping error:", err);
      
    } finally {
      setTimeout(() => {
        btn.disabled = false;
        btnText.textContent = 'Posalji';
        
        iconSuccess.classList.add('hidden');
        iconSend.classList.remove('hidden');
        statusText.classList.remove('show');
      }, 2500);
    }
  });