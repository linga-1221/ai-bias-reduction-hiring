// File upload interaction for multiple files
document.getElementById('resumeFile').addEventListener('change', function(e) {
    const fileLabel = document.getElementById('fileLabel');
    const fileList = document.getElementById('fileList');
    
    if (e.target.files.length > 0) {
        if (e.target.files.length > 20) {
            alert('Maximum 20 files allowed. Please select fewer files.');
            e.target.value = '';
            return;
        }
        
        fileLabel.innerHTML = `📄 Selected: ${e.target.files.length} file(s)`;
        fileLabel.classList.add('file-selected');
        
        // Display file list
        let fileListHTML = '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px;"><h4>Selected Files:</h4><ul>';
        for (let i = 0; i < e.target.files.length; i++) {
            fileListHTML += `<li style="margin: 5px 0;">${e.target.files[i].name} (${(e.target.files[i].size / 1024 / 1024).toFixed(2)} MB)</li>`;
        }
        fileListHTML += '</ul></div>';
        fileList.innerHTML = fileListHTML;
    } else {
        fileLabel.innerHTML = '📎 Click to select PDF files or drag & drop here (Max 20 files)';
        fileLabel.classList.remove('file-selected');
        fileList.innerHTML = '';
    }
});

// Form submission for multiple files
document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const fileInput = document.getElementById('resumeFile');
    const jobRole = document.getElementById('jobRole').value;
    
    if (!fileInput.files.length) {
        alert('Please select at least one PDF file');
        return;
    }
    
    if (!jobRole) {
        alert('Please select a job role');
        return;
    }
    
    // Add job role
    formData.append('job_role', jobRole);
    
    // Add all files
    for (let i = 0; i < fileInput.files.length; i++) {
        formData.append('resume', fileInput.files[i]);
    }
    
    document.getElementById('loading').style.display = 'block';
    document.getElementById('result').style.display = 'none';
    document.getElementById('progress-info').innerHTML = `Processing ${fileInput.files.length} resume(s)...`;
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('loading').style.display = 'none';
        const result = document.getElementById('result');
        
        if (data.error) {
            result.innerHTML = '<h3>❌ Error:</h3><p>' + data.error + '</p>';
        } else {
            let html = '<h2>📊 Batch Analysis Results</h2>';
            
            // Summary Statistics
            html += '<div class="section">';
            html += '<h3>📈 Processing Summary</h3>';
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">';
            html += `<div style="background: #e8f5e8; padding: 15px; border-radius: 10px; text-align: center;">
                        <h4 style="color: #28a745; margin: 0;">Total Files</h4>
                        <div style="font-size: 24px; font-weight: bold; color: #28a745;">${data.summary.total_files}</div>
                     </div>`;
            html += `<div style="background: #e8f5e8; padding: 15px; border-radius: 10px; text-align: center;">
                        <h4 style="color: #28a745; margin: 0;">Successful</h4>
                        <div style="font-size: 24px; font-weight: bold; color: #28a745;">${data.summary.successful}</div>
                     </div>`;
            html += `<div style="background: #ffe8e8; padding: 15px; border-radius: 10px; text-align: center;">
                        <h4 style="color: #dc3545; margin: 0;">Failed</h4>
                        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">${data.summary.failed}</div>
                     </div>`;
            html += `<div style="background: #e8f4fd; padding: 15px; border-radius: 10px; text-align: center;">
                        <h4 style="color: #0066cc; margin: 0;">Avg Match</h4>
                        <div style="font-size: 24px; font-weight: bold; color: #0066cc;">${data.summary.average_match}%</div>
                     </div>`;
            html += '</div>';
            html += '</div>';
            
            // Top Candidates
            if (data.summary.top_candidates.length > 0) {
                html += '<div class="section">';
                html += '<h3>🏆 Top Candidates</h3>';
                html += '<div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">';
                data.summary.top_candidates.forEach((candidate, index) => {
                    const matchColor = candidate.match_percentage > 70 ? '#28a745' : candidate.match_percentage > 40 ? '#f39c12' : '#e74c3c';
                    html += `<div style="background: white; margin: 10px 0; padding: 15px; border-radius: 8px; border-left: 4px solid ${matchColor};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong>${index + 1}. ${candidate.filename}</strong>
                                    <span style="color: ${matchColor}; font-weight: bold; font-size: 18px;">${candidate.match_percentage}%</span>
                                </div>
                                <div style="margin-top: 8px; color: #666;">${candidate.recommendation}</div>
                             </div>`;
                });
                html += '</div>';
                html += '</div>';
            }
            
            // Bias Analysis (same for all)
            html += '<div class="section">';
            html += '<h3>⚖️ Job Description Bias Analysis</h3>';
            if (data.bias_detected) {
                html += '<div class="bias-warning">';
                html += '<h4>⚠️ Potential Bias Detected:</h4>';
                data.bias_details.forEach(bias => {
                    html += '<div style="margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.7); border-radius: 8px;">';
                    html += '<strong>📊 ' + bias.category + ' Bias:</strong> ';
                    html += '<span style="background: #fff; padding: 3px 8px; border-radius: 15px; margin: 0 5px; border: 1px solid #f39c12;">' + bias.words.join('</span> <span style="background: #fff; padding: 3px 8px; border-radius: 15px; margin: 0 5px; border: 1px solid #f39c12;">') + '</span>';
                    html += '</div>';
                });
                html += '</div>';
            } else {
                html += '<div class="bias-safe">';
                html += '<h4>✅ Bias-Free Job Description</h4>';
                html += '<p>No significant bias detected in the job description.</p>';
                html += '</div>';
            }
            html += '</div>';
            
            // Detailed Results
            html += '<div class="section">';
            html += '<h3>📋 Detailed Results</h3>';
            html += '<div style="max-height: 600px; overflow-y: auto; background: #f8f9fa; padding: 15px; border-radius: 10px;">';
            
            data.results.forEach((result, index) => {
                if (result.status === 'success') {
                    const matchColor = result.match_percentage > 70 ? '#28a745' : result.match_percentage > 40 ? '#f39c12' : '#e74c3c';
                    html += `<div style="background: white; margin: 15px 0; padding: 20px; border-radius: 10px; border-left: 4px solid ${matchColor};">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                    <h4 style="margin: 0;">${result.filename}</h4>
                                    <span style="color: ${matchColor}; font-weight: bold; font-size: 20px;">${result.match_percentage}%</span>
                                </div>
                                
                                <div style="margin: 10px 0;">
                                    <strong>Recommendation:</strong> ${result.recommendation}
                                </div>
                                
                                <div style="margin: 15px 0;">
                                    <strong>✅ Matching Skills:</strong><br>
                                    <div style="margin-top: 8px;">`;
                    result.matching_skills.forEach(skill => {
                        html += `<span style="background: #e7f3ff; color: #0066cc; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block;">${skill}</span> `;
                    });
                    html += `</div></div>
                                
                                <div style="margin: 15px 0;">
                                    <strong>❌ Missing Skills:</strong><br>
                                    <div style="margin-top: 8px;">`;
                    result.missing_skills.forEach(skill => {
                        html += `<span style="background: #ffe8e8; color: #dc3545; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block;">${skill}</span> `;
                    });
                    html += `</div></div>
                                
                                <details style="margin-top: 15px;">
                                    <summary style="cursor: pointer; font-weight: bold;">View Anonymized Resume</summary>
                                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px; max-height: 200px; overflow-y: auto;">
                                        <pre style="white-space: pre-wrap; font-size: 12px; margin: 0;">${result.anonymized_resume}</pre>
                                    </div>
                                </details>
                             </div>`;
                } else {
                    html += `<div style="background: #ffe8e8; margin: 15px 0; padding: 20px; border-radius: 10px; border-left: 4px solid #dc3545;">
                                <h4 style="color: #dc3545; margin: 0 0 10px 0;">❌ ${result.filename}</h4>
                                <div style="color: #721c24;">Error: ${result.error}</div>
                             </div>`;
                }
            });
            
            html += '</div>';
            html += '</div>';
            
            result.innerHTML = html;
        }
        result.style.display = 'block';
    })
    .catch(error => {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('result').innerHTML = '<h3>❌ Error:</h3><p>Network error: ' + error.message + '</p>';
        document.getElementById('result').style.display = 'block';
    });
});

// Real-time bias checking
let biasCheckTimeout;
document.addEventListener('DOMContentLoaded', function() {
    const jobDescInput = document.getElementById('job-description-input');
    if (jobDescInput) {
        jobDescInput.addEventListener('input', function() {
            clearTimeout(biasCheckTimeout);
            biasCheckTimeout = setTimeout(() => {
                checkBiasRealTime(this.value);
            }, 500);
        });
    }
});

function checkBiasRealTime(text) {
    if (text.length < 10) {
        document.getElementById('bias-results').innerHTML = '';
        return;
    }
    
    fetch('/check-bias-realtime', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: text})
    })
    .then(response => response.json())
    .then(data => {
        const resultsDiv = document.getElementById('bias-results');
        let html = '';
        
        if (data.bias_detected) {
            html = '<div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin-top: 10px;">';
            html += '<strong>⚠️ Bias Detected (Score: ' + data.bias_score + ')</strong><br>';
            html += 'Biased words: ';
            data.bias_words.forEach(word => {
                html += '<span style="background: #f39c12; color: white; padding: 2px 6px; border-radius: 4px; margin: 2px;">' + word + '</span> ';
            });
            html += '</div>';
        } else {
            html = '<div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 8px; margin-top: 10px;">';
            html += '<strong>✅ No Bias Detected</strong><br>This job description appears to use inclusive language.';
            html += '</div>';
        }
        
        resultsDiv.innerHTML = html;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
