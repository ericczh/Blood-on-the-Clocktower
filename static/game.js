// 游戏页面 JavaScript
let currentSeatId = null;
let currentDayIdx = 0;
let gameData = null;
let GAME_ID = null;

// 初始化
function initGame(gameId, data) {
  GAME_ID = gameId;
  gameData = data;
  currentDayIdx = gameData.days.length - 1;
  document.getElementById('day-notes').value = gameData.days[currentDayIdx]?.notes || '';
  
  // 设置座位位置
  document.querySelectorAll('.seat-dot').forEach(seat => {
    const x = seat.dataset.x;
    const y = seat.dataset.y;
    seat.style.left = x + 'px';
    seat.style.top = y + 'px';
  });
}

function selectSeat(id) {
  id = parseInt(id, 10); // 转换为数字
  currentSeatId = id;
  const seat = gameData.seats.find(s => s.id === id);
  document.getElementById('sp-num').textContent = id;
  document.getElementById('sp-name').value = seat.playerName || '';
  document.getElementById('sp-char').value = seat.characterId || '';
  document.getElementById('sp-claimed').value = seat.claimedRole || '';
  document.getElementById('sp-alive').checked = seat.alive;
  document.getElementById('sp-vote').checked = seat.hasVote;
  document.getElementById('sp-drunk').checked = seat.drunkPoisoned;
  document.getElementById('sp-notes').value = seat.notes || '';
  document.getElementById('seatPanel').classList.remove('hidden');
}

function closeSeatPanel() {
  document.getElementById('seatPanel').classList.add('hidden');
  currentSeatId = null;
}

async function api(action, data = {}) {
  const res = await fetch(`/game/${GAME_ID}/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, ...data }),
  });
  return res.json();
}

async function saveSeat() {
  if (!currentSeatId) return;
  const data = {
    seatId: currentSeatId,
    playerName: document.getElementById('sp-name').value,
    characterId: document.getElementById('sp-char').value,
    claimedRole: document.getElementById('sp-claimed').value,
    alive: document.getElementById('sp-alive').checked,
    hasVote: document.getElementById('sp-vote').checked,
    drunkPoisoned: document.getElementById('sp-drunk').checked,
    notes: document.getElementById('sp-notes').value,
  };
  await api('update_seat', data);
  const seat = gameData.seats.find(s => s.id === currentSeatId);
  Object.assign(seat, data);
  location.reload();
}

async function addDay() {
  await api('add_day');
  location.reload();
}

function switchDay(idx) {
  idx = parseInt(idx, 10); // 转换为数字
  currentDayIdx = idx;
  document.querySelectorAll('.day-tab').forEach((el, i) => {
    el.classList.toggle('active', i === idx);
  });
  document.getElementById('day-notes').value = gameData.days[idx]?.notes || '';
}

async function saveDayNotes() {
  const notes = document.getElementById('day-notes').value;
  gameData.days[currentDayIdx].notes = notes;
  await api('update_day', { dayIndex: currentDayIdx, notes });
}

async function finishGame(winner) {
  if (!confirm(`确认 ${winner === 'good' ? '善良' : '邪恶'}阵营 胜利？`)) return;
  await api('finish', { winner });
  location.reload();
}
