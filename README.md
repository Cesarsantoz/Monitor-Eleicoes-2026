# Monitor de apuração presidencial 2026

Painel não oficial que lê dados públicos do Tribunal Superior Eleitoral. Não contém números de exemplo exibidos como se fossem reais.

## Instalação no GitHub

1. Entre em https://github.com/new e crie um repositório **público** chamado `Monitor-Eleicoes-2026` (para GitHub Pages no plano gratuito). Não use os repositórios de outros projetos.
2. Faça upload de todos os arquivos e pastas **do interior** deste pacote, preservando a pasta `.github/workflows/` (pastas que começam com ponto podem ficar ocultas em alguns exploradores). Uma forma confiável é usar Git em um computador, ou criar os arquivos pelo editor web do GitHub.
3. Abra **Settings > Actions > General > Workflow permissions** e marque **Read and write permissions**, salve. Necessário para registrar o histórico no repositório.
4. Abra **Settings > Pages > Build and deployment** e selecione **GitHub Actions** como fonte de publicação.
5. Abra **Actions > Monitor TSE - cada 10 minutos > Run workflow** para disparar a primeira consulta. Confira os logs. Execute **Publicar painel eleitoral > Run workflow**, se necessário.
6. Acompanhe o endereço: `https://cesarsantoz.github.io/Monitor-Eleicoes-2026/` depois que a publicação for concluída. O link só funcionará depois de publicar.

## Funcionamento

- O workflow `monitor.yml` consulta o JSON do TSE aproximadamente a cada 10 minutos, sem garantia de pontualidade.
- Em mudanças efetivas grava `dados/ultimo.json` e `dados/historico.csv`, em seguida salva um commit.
- O `publish.yml` publica o painel mesmo para commits feitos pelo `GITHUB_TOKEN`, utilizando o evento `workflow_run`.
- O painel faz uma verificação de novos arquivos a cada minuto, mas os dados só mudam após uma coleta bem-sucedida.
- Depois do encerramento da eleição, desative o agendamento em **Actions** para evitar execuções desnecessárias.

## Observações

O formato do JSON remoto pode mudar. Falhas de rede, indisponibilidade do TSE, limites de uso e atrasos do GitHub Actions podem afetar a coleta. Caso não haja dados, o painel exibe um aviso, não números inventados. GitHub Pages é público, inclusive quando não há URL divulgada.
