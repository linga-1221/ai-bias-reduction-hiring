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
                const h3 = document.createElement('h3');
                h3.textContent = 'Error';
                const p = document.createElement('p');
                p.textContent = data.error;
                errEl.appendChild(h3);
                errEl.appendChild(p);
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
            const h3 = document.createElement('h3');
            h3.textContent = 'Error';
            const p = document.createElement('p');
            p.textContent = 'Network error: ' + error.message;
            errEl.appendChild(h3);
            errEl.appendChild(p);
            resultDiv.appendChild(errEl);
            resultDiv.style.display = 'block';
        });
});

function buildResultsDOM(data) {
    const container = document.createElement('div');

    const title = document.createElement('h2');
    title.textContent = `Results — ${data.job_title}`;
    container.appendChild(title);

    container.appendChild(buildSummarySection(data.summary));

    if (data.summary.top_candidates.length > 0) {
        container.appendChild(buildTopCandidatesSection(data.summary.top_candidates));
    }

    container.appendChild(buildBiasSection(data.bias_detected, data.bias_details, data.bias_level, data.severity_score, data.llm_bias));
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
        { label: 'Total Files', value: summary.total_files, color: '#6c63ff', bg: '#f0eeff' },
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
        const color = c.match_percentage >= 80 ? '#27ae60' : c.match_percentage >= 60 ? '#f39c12' : c.match_percentage >= 40 ? '#fd7e14' : '#e74c3c';
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
        rec.style.cssText = 'margin-top:8px;color:#666;font-size:0.9rem;';
        rec.textContent = c.recommendation;

        card.appendChild(row);
        card.appendChild(rec);
        wrapper.appendChild(card);
    });

    section.appendChild(wrapper);
    return section;
}

function buildBiasSection(biasDetected, biasDetails, biasLevel, severityScore, llmBias) {
    const section = document.createElement('div');
    section.className = 'section';
    const h3 = document.createElement('h3');
    h3.textContent = 'Job Description Bias Analysis';
    section.appendChild(h3);

    if (biasDetected) {
        const levelColors = { low: '#ffc107', medium: '#fd7e14', high: '#dc3545' };
        const color = levelColors[biasLevel] || '#dc3545';

        const box = document.createElement('div');
        box.className = 'bias-warning';

        // Severity header
        const header = document.createElement('div');
        header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;';
        const h4 = document.createElement('h4');
        h4.style.margin = '0';
        h4.textContent = 'Bias Detected in Job Description';
        const badge = document.createElement('span');
        badge.style.cssText = `background:${color};color:white;padding:4px 12px;border-radius:20px;font-size:0.85rem;font-weight:700;`;
        badge.textContent = `${biasLevel.toUpperCase()} — Score: ${severityScore}`;
        header.appendChild(h4);
        header.appendChild(badge);
        box.appendChild(header);

        biasDetails.forEach(bias => {
            const row = document.createElement('div');
            row.style.cssText = 'margin:10px 0;padding:12px;background:rgba(255,255,255,0.8);border-radius:8px;border-left:3px solid '+color+';';

            const label = document.createElement('strong');
            label.textContent = `${bias.category} Bias (severity: ${bias.severity})`;
            row.appendChild(label);
            row.appendChild(document.createElement('br'));

            const badgeWrap = document.createElement('div');
            badgeWrap.style.margin = '8px 0';
            bias.words.forEach(word => {
                const b = document.createElement('span');
                b.style.cssText = 'background:#fff;padding:3px 8px;border-radius:12px;margin:2px;border:1px solid '+color+';font-size:0.85rem;display:inline-block;';
                b.textContent = word;
                badgeWrap.appendChild(b);
            });
            row.appendChild(badgeWrap);

            // Suggestions
            if (bias.suggestions && Object.keys(bias.suggestions).length > 0) {
                const sugLabel = document.createElement('div');
                sugLabel.style.cssText = 'font-size:0.82rem;color:#666;margin-top:6px;';
                sugLabel.textContent = '💡 Suggestions: ';
                Object.entries(bias.suggestions).forEach(([word, sug]) => {
                    sugLabel.textContent += `"${word}" → "${sug}"  `;
                });
                row.appendChild(sugLabel);
            }

            box.appendChild(row);
        });

        // LLM Explanation + Rewritten JD
        if (llmBias) {
            const llmBox = document.createElement('div');
            llmBox.style.cssText = 'margin-top:16px;background:#f0f4ff;border-radius:10px;padding:18px;border-left:4px solid #6c63ff;';
            const llmTitle = document.createElement('h4');
            llmTitle.style.cssText = 'margin:0 0 10px;color:#6c63ff;';
            llmTitle.textContent = '🤖 Gemini AI Analysis';
            llmBox.appendChild(llmTitle);
            if (llmBias.explanation) {
                const expLabel = document.createElement('strong');
                expLabel.textContent = 'Why this is biased:';
                const expText = document.createElement('p');
                expText.style.cssText = 'color:#444;font-size:0.92rem;margin:6px 0 14px;';
                expText.textContent = llmBias.explanation;
                llmBox.appendChild(expLabel);
                llmBox.appendChild(expText);
            }
            if (llmBias.rewritten_jd) {
                const rwLabel = document.createElement('strong');
                rwLabel.textContent = '✏️ AI-Rewritten (Bias-Free) Version:';
                const rwBox = document.createElement('div');
                rwBox.style.cssText = 'background:white;border-radius:8px;padding:14px;margin-top:8px;border:1px solid #dde;font-size:0.9rem;color:#333;white-space:pre-wrap;';
                rwBox.textContent = llmBias.rewritten_jd;
                llmBox.appendChild(rwLabel);
                llmBox.appendChild(rwBox);
            }
            section.appendChild(llmBox);
        }
        section.appendChild(box);
    } else {
        const box = document.createElement('div');
        box.className = 'bias-safe';
        const h4 = document.createElement('h4');
        h4.textContent = '✅ Bias-Free Job Description';
        const p = document.createElement('p');
        p.textContent = 'No significant bias detected. The language appears neutral and inclusive.';
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
    h3.textContent = `Detailed Results (${results.length} resume${results.length > 1 ? 's' : ''})`;
    section.appendChild(h3);

    const scrollBox = document.createElement('div');
    scrollBox.style.cssText = 'max-height:700px;overflow-y:auto;background:#f8f9fa;padding:15px;border-radius:10px;';

    results.forEach(result => {
        scrollBox.appendChild(result.status === 'success' ? buildSuccessCard(result) : buildFailCard(result));
    });

    section.appendChild(scrollBox);
    return section;
}

function buildSuccessCard(result) {
    const color = result.match_percentage >= 80 ? '#27ae60' : result.match_percentage >= 60 ? '#f39c12' : result.match_percentage >= 40 ? '#fd7e14' : '#e74c3c';
    const card = document.createElement('div');
    card.style.cssText = `background:white;margin:15px 0;padding:20px;border-radius:10px;border-left:4px solid ${color};`;

    const row = document.createElement('div');
    row.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;';
    const h4 = document.createElement('h4');
    h4.style.margin = '0';
    h4.textContent = result.filename;
    const pct = document.createElement('span');
    pct.style.cssText = `color:${color};font-weight:bold;font-size:22px;`;
    pct.textContent = `${result.match_percentage}%`;
    row.appendChild(h4);
    row.appendChild(pct);
    card.appendChild(row);

    const rec = document.createElement('div');
    rec.style.cssText = 'margin:8px 0 14px;padding:8px 12px;background:#f8f9fa;border-radius:6px;font-size:0.9rem;';
    const recLabel = document.createElement('strong');
    recLabel.textContent = 'Recommendation: ';
    rec.appendChild(recLabel);
    rec.appendChild(document.createTextNode(result.recommendation));
    card.appendChild(rec);

    card.appendChild(buildSkillBadges('✅ Matching Skills:', result.matching_skills, '#e7f3ff', '#0066cc'));
    card.appendChild(buildSkillBadges('❌ Missing Skills:', result.missing_skills, '#ffe8e8', '#dc3545'));

    // LLM candidate feedback
    if (result.llm_feedback && result.llm_feedback.length > 0) {
        const fbBox = document.createElement('div');
        fbBox.style.cssText = 'margin:14px 0;padding:14px;background:#f0f4ff;border-radius:8px;border-left:3px solid #6c63ff;';
        const fbTitle = document.createElement('strong');
        fbTitle.style.color = '#6c63ff';
        fbTitle.textContent = '🤖 AI Career Recommendations:';
        fbBox.appendChild(fbTitle);
        const ul = document.createElement('ul');
        ul.style.cssText = 'margin:8px 0 0 18px;padding:0;font-size:0.88rem;color:#444;';
        result.llm_feedback.forEach(tip => {
            const li = document.createElement('li');
            li.style.marginBottom = '5px';
            li.textContent = tip;
            ul.appendChild(li);
        });
        fbBox.appendChild(ul);
        card.appendChild(fbBox);
    }

    const details = document.createElement('details');
    details.style.marginTop = '14px';
    const summary = document.createElement('summary');
    summary.style.cssText = 'cursor:pointer;font-weight:600;color:#6c63ff;';
    summary.textContent = '🔒 View Anonymized Resume';
    const resumeBox = document.createElement('div');
    resumeBox.style.cssText = 'background:#f8f9fa;padding:15px;border-radius:8px;margin-top:10px;max-height:220px;overflow-y:auto;border:1px solid #e0e0e0;';
    const pre = document.createElement('pre');
    pre.style.cssText = 'white-space:pre-wrap;font-size:12px;margin:0;color:#444;';
    pre.textContent = result.anonymized_resume;
    resumeBox.appendChild(pre);
    details.appendChild(summary);
    details.appendChild(resumeBox);
    card.appendChild(details);

    return card;
}

function buildSkillBadges(label, skills, bgColor, textColor) {
    const wrapper = document.createElement('div');
    wrapper.style.margin = '12px 0';
    const strong = document.createElement('strong');
    strong.style.fontSize = '0.9rem';
    strong.textContent = label;
    wrapper.appendChild(strong);
    const badgeBox = document.createElement('div');
    badgeBox.style.marginTop = '7px';
    if (skills.length === 0) {
        const none = document.createElement('span');
        none.style.cssText = 'color:#999;font-size:0.85rem;';
        none.textContent = ' None';
        badgeBox.appendChild(none);
    } else {
        skills.forEach(skill => {
            const badge = document.createElement('span');
            badge.style.cssText = `background:${bgColor};color:${textColor};padding:4px 9px;border-radius:4px;margin:2px;display:inline-block;font-size:0.85rem;`;
            badge.textContent = skill;
            badgeBox.appendChild(badge);
        });
    }
    wrapper.appendChild(badgeBox);
    return wrapper;
}

function buildFailCard(result) {
    const card = document.createElement('div');
    card.style.cssText = 'background:#ffe8e8;margin:15px 0;padding:20px;border-radius:10px;border-left:4px solid #dc3545;';
    const h4 = document.createElement('h4');
    h4.style.cssText = 'color:#dc3545;margin:0 0 8px;';
    h4.textContent = result.filename;
    const err = document.createElement('div');
    err.style.cssText = 'color:#721c24;font-size:0.9rem;';
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
                const levelColors = { low: '#856404', medium: '#cc5200', high: '#721c24' };
                const levelBg = { low: '#fff3cd', medium: '#ffe5d0', high: '#f8d7da' };
                const tc = levelColors[data.bias_level] || '#721c24';
                const bg = levelBg[data.bias_level] || '#f8d7da';

                box.style.cssText = `background:${bg};border:1px solid ${tc};padding:15px;border-radius:8px;margin-top:10px;`;

                const header = document.createElement('div');
                header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;';
                const strong = document.createElement('strong');
                strong.textContent = `⚠ Bias Detected`;
                const scoreBadge = document.createElement('span');
                scoreBadge.style.cssText = `background:${tc};color:white;padding:2px 10px;border-radius:12px;font-size:0.82rem;font-weight:700;`;
                scoreBadge.textContent = `${data.bias_level.toUpperCase()} — Score: ${data.bias_score}`;
                header.appendChild(strong);
                header.appendChild(scoreBadge);
                box.appendChild(header);

                const wordLine = document.createElement('div');
                wordLine.style.cssText = 'font-size:0.9rem;margin-top:4px;';
                wordLine.textContent = 'Biased words: ';
                data.bias_words.forEach(word => {
                    const badge = document.createElement('span');
                    badge.style.cssText = `background:${tc};color:white;padding:2px 7px;border-radius:4px;margin:2px;font-size:0.82rem;`;
                    badge.textContent = word;
                    wordLine.appendChild(badge);
                });
                box.appendChild(wordLine);
            } else {
                box.style.cssText = 'background:#d4edda;border:1px solid #c3e6cb;padding:15px;border-radius:8px;margin-top:10px;';
                const strong = document.createElement('strong');
                strong.textContent = '✅ No Bias Detected';
                box.appendChild(strong);
                box.appendChild(document.createElement('br'));
                box.appendChild(document.createTextNode('This job description appears to use inclusive and neutral language.'));
            }

            resultsDiv.appendChild(box);
        })
        .catch(err => console.error('Bias check error:', err));
}
