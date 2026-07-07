// server.js
const express = require('express');
const mercadopago = require('mercadopago');
const app = express();
app.use(express.json());
// Configurar Mercado Pago
mercadopago.configure({
    access_token: process.env.ACCESS_TOKEN
});
// Criar preferência de pagamento (Cartão)
app.post('/create-preference', async (req, res) => {
    const { name, email, quantity, total } = req.body;
    const preference = {
        items: [{
            title: `Rifa GTA VI - ${quantity} número(s)`,
            quantity: 1,
            unit_price: total,
            currency_id: 'BRL'
        }],
        payer: {
            name: name,
            email: email
        },
        back_urls: {
            success: 'https://seusite.com/sucesso',
            failure: 'https://seusite.com/erro',
            pending: 'https://seusite.com/pendente'
        },
        auto_return: 'approved',
        payment_methods: {
            excluded_payment_types: [{ id: 'ticket' }],
            installments: 12
        }
    };
    try {
        const response = await mercadopago.preferences.create(preference);
        res.json({ init_point: response.body.init_point });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
// Criar pagamento PIX
app.post('/create-pix', async (req, res) => {
    const { name, email, total } = req.body;
    const payment = {
        transaction_amount: total,
        description: 'Rifa GTA VI',
        payment_method_id: 'pix',
        payer: {
            email: email,
            first_name: name.split(' ')[0],
            last_name: name.split(' ').slice(1).join(' ')
        }
    };
    try {
        const response = await mercadopago.payment.create(payment);
        res.json({
            qr_code: response.body.point_of_interaction.transaction_data.qr_code,
            qr_code_base64: response.body.point_of_interaction.transaction_data.qr_code_base64
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
// Webhook para notificações
app.post('/webhook', async (req, res) => {
    const { type, data } = req.body;
    if (type === 'payment') {
        const payment = await mercadopago.payment.findById(data.id);
        
        if (payment.body.status === 'approved') {
            // Registrar números vendidos no banco de dados
            console.log('Pagamento aprovado:', payment.body);
        }
    }
    res.sendStatus(200);
});
app.listen(3000, () => console.log('Servidor rodando na porta 3000'));