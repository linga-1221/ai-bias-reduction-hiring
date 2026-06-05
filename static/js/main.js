// Utility: safely escape text to prevent XSS
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Utility: show inline error instead of alert()
function showFormError(message) {
    const err = document.getElementById('form-error');
    err.textContent = message;
    err.style.display = 'block';
    setTimeout(() => { err.style.display = 'none'; }, 4000);
}

// File upload interaction for multiple files
document.getElementById('resumeFile').addEventListener('change', function(e) {
    const fileLabel = document.getElementById('fileLabel');
    const fileList = document.getElementById('fileList');

    if (e.target.files.length > 0) {
        if (e.target.files.length > 20) {
            showFormError('Maximum 20 files allowed. Please select fewer files.');
            e.target.value = '';
            return;
        }

        fileLabel.textContent = `Selected: ${e.target.files.length} file(s)`;
        fileLabel.classList.add('file-selected');

        fileList.innerHTML = '';
        const wrapper = document.createElement('div');
        wrapper.style.cssText = 'background:#f8f9fa;padding:15px;border-radius:8px;margin-top:10px;';
        const heading = document.createElement('h4');
        heading.textContent = 'Selected Files:';
        const ul = document.createElement('ul');
        for (let i = 0; i < e.target.files.length; i++) {
            const li = document.createElement('li');
            li.style.margin = '5px 0';
            li.textContent = `${e.target.files[i].name} (${(e.target.files[i].size / 1024 / 1024).toFixed(2)} MB)`;
            ul.appendChild(li);
        }
        wrapper.appendChild(heading);
        wrapper.appendChild(ul);
        fileList.appendChild(wrapper);
    } else {
        fileLabel.textContent = 'Click to select PDF files or drag & drop here (Max 20 files)';
        fileLabel.classList.remove('file-selected');
        fileList.innerHTML = '';
    }
});

// Form submission
document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const fileInput = document.getElementById('resumeFile');
    const jobRole = document.getElementById('jobRole').value;

    if (!fileInput.files.length) {
        showFormError('Please select at least one PDF file');
        return;
    }
    if (!jobRole) {
        showFormError('Please select a job role');
        return;
    }

    const formData = new FormData();
    formData.append('job_role', jobRole);
    for (let i = 0; i < fileInput.files.length; i++) {
        formData.append('resume', fileInput.files[i]);
    }

    document.getElementById('loading').style.display = 'block';
    document.getElementById('result').style.display = 'none';
    document.getElementById('progress-info').textContent = `Processing ${fileInput.files.length} resume(s)...`;

    fetch('/upload', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            document.getElementById('loading').style.display = 'none';
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '';

            if (data.error) {
                const errEl = document.createElement('div');
                errEl.innerHTML = `<h3>Error</h3><p>${escapeHtml(data.error)}</p>`;
                resultDiv.appendChild(errEl);
            } else {
                resultDiv.appendChild(buildResultsDOM(data));
            }
            resultDiv.style.display = 'block';
        })
        .catch(error => {
            document.getElementById('loading').style.display = 'none';
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '';
            const errEl = document.createElement('div');
            errEl.innerHTML = `<h3>Error</h3><p>${escapeHtml('Network error: ' + error.message)}</p>`;
            resultDiv.appendChild(errEl);
            resultDiv.style.display = 'block';
        });
});

function buildResultsDOM(data) {
    const container = document.createElement('div');

    // Title
    const title = document.createElement('h2');
    title.textContent = 'Batch Analysis Results';
    container.appendChild(title);

    // Summary
    container.appendChild(buildSummarySection(data.summary));

    // Top Candidates
    if (data.summary.top_candidates.length > 0) {
        container.appendChild(buildTopCandidatesSection(data.summary.top_candidates));
    }

    // Bias Analysis
    container.appendChild(buildBiasSection(data.bias_detected, data.bias_details));

    // Detailed Results
    container.appendChild(buildDetailedResults(data.results));

    return container;
}

function buildSummarySection(summary) {
    const section = document.createElement('div');
    section.className = 'section';
    const h3 = document.createElement('h3');
    h3.textContent = 'Processing Summary';
    section.appendChild(h3);

    const grid = document.createElement('div');
    grid.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin:20px 0;';

    const cards = [
        { label: 'Total Files', value: summary.total_files, color: '#28a745', bg: '#e8f5e8' },
        { label: 'Successful', value: summary.successful, color: '#28a745', bg: '#e8f5e8' },
        { label: 'Failed', value: summary.failed, color: '#dc3545', bg: '#ffe8e8' },
        { label: 'Avg Match', value: `${summary.average_match}%`, color: '#0066cc', bg: '#e8f4fd' }
    ];

    cards.forEach(card => {
        const div = document.createElement('div');
        div.style.cssText = `background:${card.bg};padding:15px;border-radius:10px;text-align:center;`;
        const h4 = document.createElement('h4');
        h4.style.cssText = `color:${card.color};margin:0;`;
        h4.textContent = card.label;
        const val = document.createElement('div');
        val.style.cssText = `font-size:24px;font-weight:bold;color:${card.color};`;
        val.textContent = card.value;
        div.appendChild(h4);
        div.appendChild(val);
        grid.appendChild(div);
    });

    section.appendChild(grid);
    return section;
}

function buildTopCandidatesSection(candidates) {
    const section = document.createElement('div');
    section.className = 'section';
    const h3 = document.createElement('h3');
    h3.textContent = 'Top Candidates';
    section.appendChild(h3);

    const wrapper = document.createElement('div');
    wrapper.style.cssText = 'background:#f8f9fa;padding:20px;border-radius:10px;';

    candidates.forEach((c, i) => {
        const color = c.match_percentage > 70 ? '#28a745' : c.match_percentage > 40 ? '#f39c12' : '#e74c3c';
        const card = document.createElement('div');
        card.style.cssText = `background:white;margin:10px 0;padding:15px;border-radius:8px;border-left:4px solid ${color};`;

        const row = document.createElement('div');
        row.style.cssText = 'display:flex;justify-content:space-between;align-items:center;';
        const name = document.createElement('strong');
        name.textContent = `${i + 1}. ${c.filename}`;
        const pct = document.createElement('span');
        pct.style.cssText = `color:${color};font-weight:bold;font-size:18px;`;
        pct.textContent = `${c.match_percentage}%`;
        row.appendChild(name);
        row.appendChild(pct);

        const rec = document.createElement('div');
        rec.style.cssText = 'margin-top:8px;color:#666;';
        rec.textContent = c.recommendation;

        card.appendChild(row);
        card.appendChild(rec);
        wrapper.appendChild(card);
    });

    section.appendChild(wrapper);
    return section;
}

function buildBiasSection(biasDetected, biasDetails) {
    const section = document.createElement('div');
    section.className = 'section';
    const h3 = document.createElement('h3');
    h3.textContent = 'Job Description Bias Analysis';
    section.appendChild(h3);

    if (biasDetected) {
        const box = document.createElement('div');
        box.className = 'bias-warning';
        const h4 = document.createElement('h4');
        h4.textContent = 'Potential Bias Detected:';
        box.appendChild(h4);

        biasDetails.forEach(bias => {
            const row = document.createElement('div');
            row.style.cssText = 'margin:10px 0;padding:10px;background:rgba(255,255,255,0.7);border-radius:8px;';
            const label = document.createElement('strong');
            label.textContent = `${bias.category} Bias: `;
            row.appendChild(label);
            bias.words.forEach(word => {
                const badge = document.createElement('span');
                badge.style.cssText = 'background:#fff;padding:3px 8px;border-radius:15px;margin:0 3px;border:1px solid #f39c12;';
                badge.textContent = word;
                row.appendChild(badge);
            });
            box.appendChild(row);
        });
        section.appendChild(box);
    } else {
        const box = document.createElement('div');
        box.className = 'bias-safe';
        const h4 = document.createElement('h4');
        h4.textContent = 'Bias-Free Job Description';
        const p = document.createElement('p');
        p.textContent = 'No significant bias detected in the job description.';
        box.appendChild(h4);
        box.appendChild(p);
        section.appendChild(box);
    }

    return section;
}

function buildDetailedResults(results) {
    const section = document.createElement('div');
    section.className = 'section';
    const h3 = document.createElement('h3');
    h3.textContent = 'Detailed Results';
    section.appendChild(h3);

    const scrollBox = document.createElement('div');
    scrollBox.style.cssText = 'max-height:600px;overflow-y:auto;background:#f8f9fa;padding:15px;border-radius:10px;';

    results.forEach(result => {
        if (result.status === 'success') {
            scrollBox.appendChild(buildSuccessCard(result));
        } else {
            scrollBox.appendChild(buildFailCard(result));
        }
    });

    section.appendChild(scrollBox);
    return section;
}

function buildSuccessCard(result) {
    const color = result.match_percentage > 70 ? '#28a745' : result.match_percentage > 40 ? '#f39c12' : '#e74c3c';
    const card = document.createElement('div');
    card.style.cssText = `background:white;margin:15px 0;padding:20px;border-radius:10px;border-left:4px solid ${color};`;

    const row = document.createElement('div');
    row.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;';
    const h4 = document.createElement('h4');
    h4.style.margin = '0';
    h4.textContent = result.filename;
    const pct = document.createElement('span');
    pct.style.cssText = `color:${color};font-weight:bold;font-size:20px;`;
    pct.textContent = `${result.match_percentage}%`;
    row.appendChild(h4);
    row.appendChild(pct);
    card.appendChild(row);

    const rec = document.createElement('div');
    rec.style.margin = '10px 0';
    const recLabel = document.createElement('strong');
    recLabel.textContent = 'Recommendation: ';
    rec.appendChild(recLabel);
    rec.appendChild(document.createTextNode(result.recommendation));
    card.appendChild(rec);

    card.appendChild(buildSkillBadges('Matching Skills:', result.matching_skills, '#e7f3ff', '#0066cc'));
    card.appendChild(buildSkillBadges('Missing Skills:', result.missing_skills, '#ffe8e8', '#dc3545'));

    const details = document.createElement('details');
    details.style.marginTop = '15px';
    const summary = document.createElement('summary');
    summary.style.cssText = 'cursor:pointer;font-weight:bold;';
    summary.textContent = 'View Anonymized Resume';
    const resumeBox = document.createElement('div');
    resumeBox.style.cssText = 'background:#f8f9fa;padding:15px;border-radius:8px;margin-top:10px;max-height:200px;overflow-y:auto;';
    const pre = document.createElement('pre');
    pre.style.cssText = 'white-space:pre-wrap;font-size:12px;margin:0;';
    pre.textContent = result.anonymized_resume;
    resumeBox.appendChild(pre);
    details.appendChild(summary);
    details.appendChild(resumeBox);
    card.appendChild(details);

    return card;
}

function buildSkillBadges(label, skills, bgColor, textColor) {
    const wrapper = document.createElement('div');
    wrapper.style.margin = '15px 0';
    const strong = document.createElement('strong');
    strong.textContent = label;
    wrapper.appendChild(strong);
    const badgeBox = document.createElement('div');
    badgeBox.style.marginTop = '8px';
    skills.forEach(skill => {
        const badge = document.createElement('span');
        badge.style.cssText = `background:${bgColor};color:${textColor};padding:4px 8px;border-radius:4px;margin:2px;display:inline-block;`;
        badge.textContent = skill;
        badgeBox.appendChild(badge);
    });
    wrapper.appendChild(badgeBox);
    return wrapper;
}

function buildFailCard(result) {
    const card = document.createElement('div');
    card.style.cssText = 'background:#ffe8e8;margin:15px 0;padding:20px;border-radius:10px;border-left:4px solid #dc3545;';
    const h4 = document.createElement('h4');
    h4.style.cssText = 'color:#dc3545;margin:0 0 10px 0;';
    h4.textContent = result.filename;
    const err = document.createElement('div');
    err.style.color = '#721c24';
    err.textContent = `Error: ${result.error}`;
    card.appendChild(h4);
    card.appendChild(err);
    return card;
}

// Real-time bias checking
let biasCheckTimeout;
document.addEventListener('DOMContentLoaded', function() {
    const jobDescInput = document.getElementById('job-description-input');
    if (jobDescInput) {
        jobDescInput.addEventListener('input', function() {
            clearTimeout(biasCheckTimeout);
            biasCheckTimeout = setTimeout(() => checkBiasRealTime(this.value), 500);
        });
    }
});

function checkBiasRealTime(text) {
    const resultsDiv = document.getElementById('bias-results');
    if (text.length < 10) {
        resultsDiv.innerHTML = '';
        return;
    }

    fetch('/check-bias-realtime', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
    })
        .then(response => response.json())
        .then(data => {
            resultsDiv.innerHTML = '';
            const box = document.createElement('div');

            if (data.bias_detected) {
                box.style.cssText = 'background:#fff3cd;border:1px solid #ffeaa7;padding:15px;border-radius:8px;margin-top:10px;';
                const strong = document.createElement('strong');
                strong.textContent = `Bias Detected (Score: ${data.bias_score})`;
                box.appendChild(strong);
                box.appendChild(document.createElement('br'));
                box.appendChild(document.createTextNode('Biased words: '));
                data.bias_words.forEach(word => {
                    const badge = document.createElement('span');
                    badge.style.cssText = 'background:#f39c12;color:white;padding:2px 6px;border-radius:4px;margin:2px;';
                    badge.textContent = word;
                    box.appendChild(badge);
                });
            } else {
                box.style.cssText = 'background:#d4edda;border:1px solid #c3e6cb;padding:15px;border-radius:8px;margin-top:10px;';
                const strong = document.createElement('strong');
                strong.textContent = 'No Bias Detected';
                box.appendChild(strong);
                box.appendChild(document.createElement('br'));
                box.appendChild(document.createTextNode('This job description appears to use inclusive language.'));
            }

            resultsDiv.appendChild(box);
        })
        .catch(err => console.error('Bias check error:', err));
}
