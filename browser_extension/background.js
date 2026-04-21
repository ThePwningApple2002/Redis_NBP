chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "sendToWebhook") {
      
      const WEBHOOK_URL = "http://127.0.0.1:8000/webhook";  
      const payload = {
        sourceUrl: sender.tab ? sender.tab.url : "Unknown URL",
        title: sender.tab ? sender.tab.title : "Unknown Title",
        timestamp: new Date().toISOString(),
        html: request.data
      };
  
      fetch(WEBHOOK_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      })
      .then(response => {
        if (response.ok) {
          console.log("Successfully sent HTML to webhook!");
        } else {
          console.error("Webhook responded with an error:", response.status);
        }
      })
      .catch(error => {
        console.error("Network error while sending to webhook:", error);
      });
    }
    
    return true; 
  });