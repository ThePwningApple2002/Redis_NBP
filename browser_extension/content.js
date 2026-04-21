{
    const getMetaTag = (name) => {
        const tag = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
        return tag ? tag.getAttribute('content') : '';
    };
    
    const siteScrapers = {
        "web.coolinarika.com": () => {
            console.log("Pokreće se Coolinarika skrejper...");
            
            const ingredientsBlock = document.querySelector('.css-12a8hbn');
            const instructionsBlock = document.querySelector('.css-1odmerm');
            
            let finalHTML = "";
            
            if (ingredientsBlock) {
                finalHTML += ingredientsBlock.outerHTML;
            }
            if (instructionsBlock) {
                finalHTML += instructionsBlock.outerHTML;
            }
            
            return {
                htmlFragment: finalHTML !== "" ? finalHTML : "<p>Sadržaj recepta nije pronađen.</p>"
            };
        },  
        "recepti.zena.blic.rs": () => {
            console.log("Pokreće se Blic Zena skrejper...");
            
            const ingredientsBlock = document.querySelector('.ingredients');
            const instructionsBlock = document.querySelector('.instructions');
            
            let finalHTML = "";
            
            if (ingredientsBlock) {
                finalHTML += ingredientsBlock.outerHTML;
            }
            if (instructionsBlock) {
                finalHTML += instructionsBlock.outerHTML;
            }
            
            return {
                htmlFragment: finalHTML !== "" ? finalHTML : "<p>Sadržaj recepta nije pronađen.</p>"
            };
        },

        "default": () => {
            console.log("Website not recognized. Using default fallback scraper...");
            const mainContent = document.querySelector('article') || 
                                document.querySelector('main') || 
                                document.body;
            return {
                htmlFragment: mainContent.innerHTML
            };
        }
    };

    const currentDomain = window.location.hostname;

    const scraperToRun = siteScrapers[currentDomain] || siteScrapers["default"];

    const scrapedData = scraperToRun();

    const payload = {
        url: window.location.href,
        title: document.title,
        description: getMetaTag('description') || getMetaTag('og:description'),
        siteName: getMetaTag('og:site_name') || currentDomain,
        htmlFragment: scrapedData.htmlFragment 
    };

    chrome.runtime.sendMessage({ 
        action: "sendToWebhook", 
        data: payload 
    });
}