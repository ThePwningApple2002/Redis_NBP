chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "sendToWebhook") {
      
      const WEBHOOK_URL = "http://127.0.0.1:8000/recipes/ingest";  
      const payload = {
        url: request.data.url || (sender.tab ? sender.tab.url : "Unknown URL"),
        title: request.data.title || (sender.tab ? sender.tab.title : "Unknown Title"),
        description: request.data.description || null,
        siteName: request.data.siteName || null,
        htmlFragment: request.data.htmlFragment || request.data.html,
        sourceUrl: sender.tab ? sender.tab.url : "Unknown URL",
        timestamp: new Date().toISOString()
      };
      
      console.log("Sending payload to backend:", payload);
  
      fetch(WEBHOOK_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      })
      .then(response => {
        console.log("Response status:", response.status);
        if (response.ok) {
          console.log("Successfully sent HTML to webhook!");
          sendResponse({success: true});
        } else {
          return response.json().then(err => {
            console.error("Webhook responded with an error:", response.status, err);
            sendResponse({success: false, error: err});
          });
        }
      })
      .catch(error => {
        console.error("Network error while sending to webhook:", error);
        sendResponse({success: false, error: error.message});
      });
      
      return true;
    }
  });