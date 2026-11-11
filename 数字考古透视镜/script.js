const glass = document.getElementById('magnifying-glass'), aiLog = document.getElementById('ai-log'), steps = [document.getElementById('step-0'), document.getElementById('step-1'), document.getElementById('step-2'), document.getElementById('step-3')];
let currentChar = '', animationSequence = null, isScrolling = false, scrollTimeout = null;
function getCharAtPoint(x, y) {
    if (document.caretRangeFromPoint) {
        const range = document.caretRangeFromPoint(x, y);
        if (range && range.startContainer.nodeType === Node.TEXT_NODE) return range.startContainer.textContent.charAt(range.startOffset);
    }
    return null;
}
function showChar(char, x, y) {
    if (isScrolling) return;
    if (char && /[\u4e00-\u9fa5]/.test(char)) {
        if (char !== currentChar) startThreeStepAnimation(char);
        glass.style.left = x + 'px';
        glass.style.top = y + 'px';
        glass.classList.add('active');
    } else {
        glass.classList.remove('active');
        currentChar = '';
        stopAnimation();
    }
}
document.addEventListener('mousemove', e => { showChar(getCharAtPoint(e.clientX, e.clientY), e.clientX, e.clientY); });
document.addEventListener('touchstart', e => { clearTimeout(scrollTimeout); }, { passive: true });
document.addEventListener('touchmove', e => {
    isScrolling = true;
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => { isScrolling = false; }, 300);
    const touch = e.touches[0];
    showChar(getCharAtPoint(touch.clientX, touch.clientY), touch.clientX, touch.clientY);
}, { passive: true });
document.addEventListener('touchend', () => { scrollTimeout = setTimeout(() => { isScrolling = false; }, 300); }, { passive: true });
function startThreeStepAnimation(char) { currentChar = char; stopAnimation(); const codePoint = char.charCodeAt(0), hex = codePoint.toString(16).toUpperCase().padStart(4, '0'), bin = codePoint.toString(2).padStart(16, '0'); document.getElementById('val-char').textContent = char; document.getElementById('val-unicode').textContent = 'U+' + hex; document.getElementById('val-binary').innerHTML = bin.split('').map(b => '<div class="bit">' + b + '</div>').join(''); const utf8Bytes = Array.from(unescape(encodeURIComponent(char))).map(c => c.charCodeAt(0)); document.getElementById('val-utf8').innerHTML = utf8Bytes.map((byte, i) => { const bStr = byte.toString(2).padStart(8, '0'), marker = i === 0 ? (utf8Bytes.length === 3 ? '1110' : utf8Bytes.length === 2 ? '110' : '0') : '10'; return '<div class="box"><span class="marker">' + marker + '</span><span class="data">' + bStr.substring(marker.length) + '</span></div>'; }).join(''); playSequence(0); updateAiLog(char, hex, bin, utf8Bytes); }
function playSequence(index) { steps.forEach(s => s.classList.remove('active', 'exit')); if (index > 0) steps[index-1].classList.add('exit'); steps[index].classList.add('active'); animationSequence = setTimeout(() => { if (index < steps.length - 1) playSequence(index + 1); else playSequence(0); }, index === 0 ? 1000 : index === 3 ? 3000 : 1500); }
function stopAnimation() { clearTimeout(animationSequence); steps.forEach(s => s.classList.remove('active', 'exit')); }
function updateAiLog(char, hex, bin, utf8Bytes) { const card = document.createElement('div'); card.className = 'ai-note-card'; card.innerHTML = '<strong>数字化考古：汉字「' + char + '」</strong>1. <b>查户口</b>：在万国码(Unicode)中找到身份证号 <u>' + hex + '</u>。<br>2. <b>变数字</b>：将编号转为计算机识别的二进制 <u>' + bin.substring(0,8) + '...</u>。<br>3. <b>装箱子</b>：按照UTF-8规则封装为 <u>' + utf8Bytes.length + '个字节</u>。紫色为"暗号"引导位，绿色为数据位。'; aiLog.prepend(card); if (aiLog.children.length > 5) aiLog.removeChild(aiLog.lastChild); }