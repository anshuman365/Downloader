// Quality options setup
function initQualitySelector() {
    const mediaTypeSelect = document.getElementById('media-type-select');
    const qualitySelect = document.getElementById('quality-select');
    
    if (!mediaTypeSelect || !qualitySelect) return;
    
    // Define quality options
    const audioQualities = {
        '32k': '32kbps',
        '64k': '64kbps',
        '128k': '128kbps',
        '192k': '192kbps (Default)',
        '256k': '256kbps',
        '320k': '320kbps'
    };
    
    const videoQualities = {
        '144p': '144p',
        '240p': '240p',
        '360p': '360p',
        '480p': '480p',
        '720p': '720p (HD)',
        '1080p': '1080p (Full HD)',
        '1440p': '1440p (2K)',
        '2160p': '2160p (4K)'
    };
    
    // Function to update quality options
    function updateQualityOptions() {
        const isAudio = mediaTypeSelect.value === 'audio';
        const qualities = isAudio ? audioQualities : videoQualities;
        
        // Clear existing options
        qualitySelect.innerHTML = '';
        
        // Add new options
        for (const [key, value] of Object.entries(qualities)) {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = value;
            
            // Set default selection
            if (key === (isAudio ? '192k' : '720p')) {
                option.selected = true;
            }
            
            qualitySelect.appendChild(option);
        }
    }
    
    // Initial setup
    updateQualityOptions();
    
    // Update options when media type changes
    mediaTypeSelect.addEventListener('change', updateQualityOptions);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initQualitySelector();
    
    // Search functionality
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    let searchTimeout;
    
    if (searchInput && searchResults) {
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            clearTimeout(searchTimeout);
            
            if (query.length < 2) {
                searchResults.style.display = 'none';
                return;
            }
            
            searchResults.innerHTML = '<div class="search-loading">Searching YouTube...</div>';
            searchResults.style.display = 'block';
            
            // Debounce search
            searchTimeout = setTimeout(() => {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(response => {
                        if (!response.ok) throw new Error('Network response was not ok');
                        return response.json();
                    })
                    .then(results => {
                        if (results.length === 0) {
                            searchResults.innerHTML = '<div class="no-results">No results found</div>';
                            return;
                        }
                        
                        searchResults.innerHTML = '';
                        results.forEach(item => {
                            const resultItem = document.createElement('div');
                            resultItem.className = 'result-item';
                            resultItem.dataset.url = item.url;
                            resultItem.dataset.title = item.title;
                            
                            resultItem.innerHTML = `
                                ${item.thumbnail ? `<img src="${item.thumbnail}" class="thumbnail" alt="Thumbnail">` : ''}
                                <div class="result-details">
                                    <div class="result-title">${item.title}</div>
                                    <div class="result-duration">${item.duration || ''}</div>
                                </div>
                            `;
                            
                            resultItem.addEventListener('click', () => {
                                downloadSelectedItem(item.url, item.title);
                            });
                            
                            searchResults.appendChild(resultItem);
                        });
                    })
                    .catch(error => {
                        console.error('Search error:', error);
                        searchResults.innerHTML = '<div class="no-results">Error loading results</div>';
                    });
            }, 500);
        });
        
        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchResults.contains(e.target) {
                searchResults.style.display = 'none';
            }
        });
    }
    
    function downloadSelectedItem(url, title) {
        const mediaType = document.querySelector('select[name="media_type"]').value;
        const quality = document.querySelector('select[name="quality"]').value;
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/add';
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (csrfToken) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            csrfInput.value = csrfToken;
            form.appendChild(csrfInput);
        }
        
        const urlInput = document.createElement('input');
        urlInput.type = 'hidden';
        urlInput.name = 'input';
        urlInput.value = url;
        form.appendChild(urlInput);
        
        const typeInput = document.createElement('input');
        typeInput.type = 'hidden';
        typeInput.name = 'media_type';
        typeInput.value = mediaType;
        form.appendChild(typeInput);
        
        const qualityInput = document.createElement('input');
        qualityInput.type = 'hidden';
        qualityInput.name = 'quality';
        qualityInput.value = quality;
        form.appendChild(qualityInput);
        
        document.body.appendChild(form);
        form.submit();
        
        if (searchResults) {
            searchResults.innerHTML = `<div class="search-loading">Adding "${title}" to download queue...</div>`;
            
            setTimeout(() => {
                searchInput.value = '';
                searchResults.style.display = 'none';
            }, 2000);
        }
    }
});