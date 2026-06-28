const CONFIG = {
    pricePerNumber: (window.APP_CONFIG && window.APP_CONFIG.pricePerNumber) || 10,
    drawDate: new Date('2026-11-19T20:00:00'),
    totalNumbers: 100
};

let selectedQuantity = 5;
let selectedPayment = 'pix';
let soldNumbers = [7, 15, 23, 42, 58, 67, 89];

document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    startCountdown();
    renderNumbers();
    setupEventListeners();
    updateTotal();
});

function createParticles() {
    const container = document.getElementById('particles');
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 15 + 's';
        particle.style.animationDuration = (10 + Math.random() * 10) + 's';
        container.appendChild(particle);
    }
}

function startCountdown() {
    function updateCountdown() {
        const now = new Date();
        const diff = CONFIG.drawDate - now;
        if (diff <= 0) {
            document.getElementById('days').textContent = '00';
            document.getElementById('hours').textContent = '00';
            document.getElementById('minutes').textContent = '00';
            document.getElementById('seconds').textContent = '00';
            return;
        }
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        document.getElementById('days').textContent = String(days).padStart(2, '0');
        document.getElementById('hours').textContent = String(hours).padStart(2, '0');
        document.getElementById('minutes').textContent = String(minutes).padStart(2, '0');
        document.getElementById('seconds').textContent = String(seconds).padStart(2, '0');
    }
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

function renderNumbers() {
    const grid = document.getElementById('numbersGrid');
    grid.innerHTML = '';
    for (let i = 1; i <= CONFIG.totalNumbers; i++) {
        const slot = document.createElement('div');
        slot.className = 'number-slot';
        slot.textContent = String(i).padStart(2, '0');
        if (soldNumbers.includes(i)) {
            slot.classList.add('sold');
            slot.title = 'Número já vendido';
        } else {
            slot.classList.add('available');
            slot.onclick = () => selectNumber(slot);
        }
        grid.appendChild(slot);
    }
}

function selectNumber(slot) {
    if (slot.classList.contains('sold')) return;
    slot.classList.toggle('selected');
    updateSelectedNumbers();
}

function updateSelectedNumbers() {
    const selected = document.querySelectorAll('.number-slot.selected');
    selectedQuantity = selected.length || 1;
    document.querySelectorAll('.qty-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById('customQty').value = '';
    updateTotal();
}

function setupEventListeners() {
    document.querySelectorAll('.qty-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.qty-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedQuantity = parseInt(btn.dataset.qty, 10);
            document.getElementById('customQty').value = '';
            document.querySelectorAll('.number-slot.selected').forEach(el => el.classList.remove('selected'));
            updateTotal();
        });
    });

    document.getElementById('customQty').addEventListener('input', (e) => {
        const value = parseInt(e.target.value, 10);
        if (value > 0) {
            document.querySelectorAll('.qty-btn').forEach(b => b.classList.remove('active'));
            selectedQuantity = value;
            document.querySelectorAll('.number-slot.selected').forEach(el => el.classList.remove('selected'));
            updateTotal();
        }
    });

    document.querySelectorAll('.payment-option').forEach(option => {
        option.addEventListener('click', () => {
            document.querySelectorAll('.payment-option').forEach(o => o.classList.remove('selected'));
            option.classList.add('selected');
            selectedPayment = option.dataset.method;
        });
    });

    document.getElementById('purchaseForm').addEventListener('submit', handlePurchase);

    document.getElementById('phone').addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 11) value = value.slice(0, 11);
        if (value.length > 6) {
            value = `(${value.slice(0, 2)}) ${value.slice(2, 7)}-${value.slice(7)}`;
        } else if (value.length > 2) {
            value = `(${value.slice(0, 2)}) ${value.slice(2)}`;
        }
        e.target.value = value;
    });

    window.onclick = function(event) {
        const modal = document.getElementById('pixModal');
        if (event.target === modal) {
            closeModal();
        }
    };
}

function updateTotal() {
    const total = selectedQuantity * CONFIG.pricePerNumber;
    document.getElementById('totalAmount').textContent = `R$ ${total.toFixed(2).replace('.', ',')}`;
}

async function handlePurchase(e) {
    e.preventDefault();

    const formData = {
        name: document.getElementById('name').value.trim(),
        email: document.getElementById('email').value.trim(),
        phone: document.getElementById('phone').value.trim(),
        quantity: selectedQuantity,
        paymentMethod: selectedPayment
    };

    if (!formData.name || !formData.email || !formData.phone) {
        alert('Preencha todos os campos obrigatórios.');
        return;
    }

    try {
        const clientRes = await fetch('/clientes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const clientData = await clientRes.json();
        if (!clientRes.ok || clientData.erro) {
            alert(`Falha no cadastro: ${clientData.erro || 'Erro desconhecido'}`);
            return;
        }

        const prefRes = await fetch('/create-preference', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const prefData = await prefRes.json();
        if (!prefRes.ok || prefData.erro) {
            alert(`Falha ao iniciar pagamento: ${prefData.erro || 'Erro desconhecido'}`);
            return;
        }

        if (prefData.init_point) {
            window.location.href = prefData.init_point;
            return;
        }

        alert('Pagamento criado, mas URL de checkout indisponível.');
    } catch (error) {
        console.error('Erro no processo de compra:', error);
        alert('Erro de rede ao processar compra.');
    }
}

function closeModal() {
    const modal = document.getElementById('pixModal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
}

function copyPix() {
    const pixCode = document.getElementById('pixCode').textContent;
    navigator.clipboard.writeText(pixCode).then(() => {
        alert('Código PIX copiado para a área de transferência!');
    });
}
