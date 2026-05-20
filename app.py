from flask import Flask, jsonify, render_template_string
import random
import time
from datetime import datetime, timedelta

app = Flask(__name__)

historico_grafico = {}

# Lista simplificada para o teste nao travar
ESTADOS = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']

@app.route('/api/status/<estado>/<tipo_nota>')
def get_status(estado, tipo_nota):
    estado = estado.upper()
    tipo_nota = tipo_nota.upper()
    agora = datetime.now().strftime("%H:%M")
    
    # Teste simulado ultra rapido para evitar travamento de rede local
    if estado == 'AM':
        regua_status, label_ping = random.choice([(4, "Timeout"), (5, "Erro")]), "Falha"
    else:
        regua_status, label_ping = 1, f"{random.randint(40, 120)}ms"
        
    chave = f"{estado}_{tipo_nota}"
    
    if chave not in historico_grafico:
        historico_grafico[chave] = []
        base_tempo = datetime.now()
        for i in range(10, 0, -1):
            ponto_hora = base_tempo - timedelta(minutes=i)
            h_status = random.choice([1, 2, 5]) if estado == 'AM' else 1
            h_ping = "Erro" if estado == 'AM' else f"{random.randint(40, 120)}ms"
            historico_grafico[chave].append({"horario": ponto_hora.strftime("%H:%M"), "status": h_status, "ping": h_ping})

    if not historico_grafico[chave] or historico_grafico[chave][-1]["horario"] != agora:
        historico_grafico[chave].append({"horario": agora, "status": regua_status, "ping": label_ping})
    if len(historico_grafico[chave]) > 15:
        historico_grafico[chave].pop(0)

    return jsonify({"estado": estado, "tipo": tipo_nota, "status_atual": regua_status, "historico": historico_grafico[chave]})

@app.route('/')
def index():
    return render_template_string(HTML_FRONTEND)

HTML_FRONTEND = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Consulta Sefaz</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #0b0f19; color: white; font-family: sans-serif; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-bottom: 20px; }
        @media (min-width: 600px) { .grid { grid-template-columns: repeat(14, 1fr); } }
        .btn-est { padding: 10px 0; text-align: center; border-radius: 6px; font-weight: bold; font-size: 12px; cursor: pointer; border: 1px solid transparent; }
        .normal { bg-color: rgba(34, 197, 94, 0.2); background: rgba(34, 197, 94, 0.2); color: #4ade80; border-color: rgba(34, 197, 94, 0.3); }
        .alerta { bg-color: rgba(245, 158, 11, 0.2); background: rgba(245, 158, 11, 0.2); color: #fbbf24; border-color: rgba(245, 158, 11, 0.3); }
        .erro { bg-color: rgba(239, 68, 68, 0.2); background: rgba(239, 68, 68, 0.2); color: #f87171; border-color: rgba(239, 68, 68, 0.3); }
        .ativo { outline: 2px solid #fbbf24; transform: scale(1.05); }
        .container { max-width: 1100px; margin: 0 auto; background: #1e293b; padding: 20px; border-radius: 8px; }
        .header { display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 20px; }
        .btn-tipo { padding: 8px 16px; background: #334155; border: none; color: white; border-radius: 4px; cursor: pointer; margin-right: 5px; font-weight: bold; }
        .btn-tipo.active { background: #fbbf24; color: #0f172a; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💻 Consulta Sefaz</h1>
            <div style="color: #4ade80;">● MONITOR ATIVO</div>
        </div>
        <div style="margin-bottom: 20px;">
            <button id="b-NFe" class="btn-tipo active" onclick="mudarTipo('NFe')">NFe</button>
            <button id="b-NFCe" class="btn-tipo" onclick="mudarTipo('NFCe')">NFCe</button>
            <button id="b-CTe" class="btn-tipo" onclick="mudarTipo('CTe')">CTe</button>
            <button id="b-MDFe" class="btn-tipo" onclick="mudarTipo('MDFe')">MDFe</button>
        </div>
        <div class="grid" id="box-estados"></div>
        <div style="background: #0f172a; padding: 20px; border-radius: 6px; height: 350px;">
            <canvas id="meuGrafico"></canvas>
        </div>
    </div>
    <script>
        const estados = ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO'];
        let estadoAtivo = 'AM', tipoAtivo = 'NFe', chart = null;
        
        const box = document.getElementById('box-estados');
        estados.forEach(e => {
            const b = document.createElement('div');
            b.id = 'btn-' + e; b.innerText = e; b.className = 'btn-est normal';
            b.onclick = () => { estadoAtivo = e; rodar(); };
            box.appendChild(b);
        });

        function g(labels, dados, pings) {
            if(chart) chart.destroy();
            chart = new Chart(document.getElementById('meuGrafico').getContext('2d'), {
                type: 'line', data: { labels: labels, datasets: [{ data: dados, borderColor: '#fbbf24', backgroundColor: 'rgba(251, 191, 36, 0.05)', borderWidth: 3, pointRadius: 6, pings: pings }]},
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: 1, max: 5, ticks: { color: '#94a3b8', callback: function(v){ return {1:'Normal: <= 2s', 2:'Lento', 3:'Muito lento', 4:'Timeout', 5:'Erro'}[v]; }}}, x: { ticks: { color: '#94a3b8' }}}, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function(c){ return 'Resposta: ' + c.dataset.pings[c.dataIndex]; }}}}}
            });
        }

        async function rodar() {
            for(let e of estados) {
                try {
                    const r = await fetch('/api/status/' + e + '/' + tipoAtivo);
                    const d = await r.json();
                    const b = document.getElementById('btn-' + e);
                    b.className = 'btn-est ' + (d.status_atual === 1 ? 'normal' : d.status_atual <= 3 ? 'alerta' : 'erro');
                    if(e === estadoAtivo) {
                        b.classList.add('ativo');
                        g(d.historico.map(h=>h.horario), d.historico.map(h=>h.status), d.historico.map(h=>h.ping));
                    }
                } catch(err){}
            }
        }

        function mudarTipo(t) {
            document.getElementById('b-' + tipoAtivo).classList.remove('active');
            tipoAtivo = t;
            document.getElementById('b-' + t).classList.add('active');
            rodar();
        }

        rodar(); setInterval(rodar, 15000);
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)