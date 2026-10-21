// Joga sozinho o episódio aberto (para teste): sempre a resposta certa, exceto 'erros' propositais.
window.autoplay = async (maxMs = 240000) => {
  const t0 = Date.now(), wait = (ms) => new Promise(r => setTimeout(r, ms));
  const log = [];
  while (Date.now() - t0 < maxMs) {
    await wait(120);
    if (document.querySelector('.verdict')) return {fim: document.querySelector('.stamp').textContent, xp: document.querySelector('.verdict .xp').textContent, cred: G && G.cred, erros: G && G.erros, log};
    const c = EP && G && EP.cenas[G.scene];
    const modal = document.querySelector('.modal');
    if (modal && c) {
      const want = c.tipo === 'depoimento' ? c.contradicao.provas[0] : c.provas[0];
      const p = EP.provas.find(x => x.id === want);
      const tabs = [...modal.querySelectorAll('.tabs2 button')];
      tabs[p.tipo === 'lei' ? 1 : 0].click(); await wait(80);
      const ev = [...modal.querySelectorAll('.ev')].find(b => b.textContent.includes(p.nome));
      if (!ev) { log.push('prova ausente nos autos: ' + want); modal.querySelector('.x').click(); continue; }
      ev.click(); await wait(60); modal.querySelector('.pbtn:not(.sec)').click(); continue;
    }
    if (document.querySelector('.spot')) {
      const s = [...document.querySelectorAll('.spot')].find(x => !x.classList.contains('seen'));
      if (s) { s.click(); continue; }
      const cv = [...document.querySelectorAll('.inv-panel button:not(.go)')].find(b => !b.classList.contains('done'));
      if (cv) { cv.click(); continue; }
      const go = document.querySelector('.inv-panel .go');
      if (go.disabled) { log.push('travou na investigação ' + G.scene); return {erro: 'investigação travada', log}; }
      go.click(); continue;
    }
    if (G && G.xkeys) {
      const m = /Afirmação (\d+)/.exec(document.querySelector('#keys').textContent || '');
      if (!m) continue;
      G.xkeys(Number(m[1]) - 1 === c.contradicao.afirmacao ? 'present' : 'next'); continue;
    }
    if (G && G.choiceKeys) { G.choiceKeys(c.livre ? 0 : c.opcoes.findIndex(o => o.certa)); continue; }
    if (G && G.decideKeys) { G.decideKeys(c.correta); continue; }
    if (advance) advance();
  }
  return {erro: 'tempo esgotado', cena: G && G.scene, log};
};
