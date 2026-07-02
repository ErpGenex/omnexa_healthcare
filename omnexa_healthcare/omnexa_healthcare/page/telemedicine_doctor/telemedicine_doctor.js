frappe.pages['telemedicine_doctor'].on_page_load = function(wrapper) {
    var $wrapper = $(wrapper);
    
    // Clear any existing content to prevent duplication
    $wrapper.empty();
    
    // Remove any existing iframe styles
    $('.page-content').css({
        'height': '100vh',
        'overflow': 'hidden',
        'background': '#f7fafc'
    });
    
    // Create unique ID for this instance
    var iframeId = 'telemedicine-doctor-iframe-' + Date.now();
    
    $wrapper.html(`
        <div style="width: 100%; height: calc(100vh - 100px); display: flex; flex-direction: column; background: #f7fafc; position: relative;">
            <div id="${iframeId}-loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
                <div style="font-size: 24px; color: #666;">جاري التحميل...</div>
            </div>
            <iframe id="${iframeId}" 
                    src="/telemedicine-doctor" 
                    style="flex: 1; width: 100%; border: none; background: #fff; opacity: 0; transition: opacity 0.3s;" 
                    frameborder="0"
                    onload="document.getElementById('${iframeId}-loading').style.display='none'; this.style.opacity = 1;"
                    onerror="document.getElementById('${iframeId}-loading').innerHTML='<div style=\\'color: red;\\'>فشل التحميل. <a href=\\'/telemedicine-doctor\\' target=\\'_blank\\'>افتح في نافذة جديدة</a></div>'">
            </iframe>
        </div>
    `);
};
