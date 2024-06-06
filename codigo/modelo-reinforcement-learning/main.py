import time

import streamlit as st
import os
import threading
from train import ProcessMatch
import plotly.express as px
import pandas as pd

# Function to run the matching process in a separate thread
def run_matching(process_match_instance):
    process_match_instance.run()
    st.session_state["matching_in_progress"] = False
    st.session_state["matching_done"] = True

models_dir = "./models"
model_files = os.listdir(models_dir)
model_options = [model_file for model_file in model_files if model_file.endswith(".pth")]

st.sidebar.title("Upload de arquivos")

selected_model = st.sidebar.selectbox("Selecionar Modelo", model_options)

file_compras = st.sidebar.file_uploader("Tabela de Compras", type=["csv"], key="fileCompras")
file_vendas = st.sidebar.file_uploader("Tabela de Vendas", type=["csv"], key="fileVendas")

#Button to start matching process
if st.sidebar.button('Iniciar Casamentos'):
    if file_compras is not None and file_vendas is not None:
        st.session_state["matching_in_progress"] = True
        process_match = ProcessMatch(file_vendas, file_compras)
        st.write("Total de Vendas: ", process_match.total_to_match)
        model_path = os.path.join(models_dir, selected_model)
        process_match.load_model(model_path)
        st.session_state["process_match"] = process_match
        matching_thread = threading.Thread(target=run_matching, args=(process_match,))
        matching_thread.start()
        st.session_state["start_time"] = time.time()
    else:
        st.sidebar.write("Por favor, carregue ambos os arquivos antes de iniciar.")

progress_bar = st.empty()
progress_text = st.empty()

# Check if matching process is in progress
if "matching_in_progress" in st.session_state and st.session_state["matching_in_progress"]:
    if st.sidebar.button("Stop"):
        process_match = st.session_state["process_match"]
        process_match.request_stop()
        st.session_state["matching_in_progress"] = False
        st.warning("Processamento parado.")
    else:
        process_match = st.session_state["process_match"]
        if process_match.total_to_match > 0:
            while st.session_state["matching_in_progress"]:
                time.sleep(1)
                elapsed_time = time.time() - st.session_state["start_time"]
                if process_match.total_to_match > 0:
                    progress = process_match.match_count / process_match.total_to_match
                    progress_bar.progress(progress)
                    progress_text.text(f"Matches per second: {process_match.match_count / elapsed_time:.2f}")
                if process_match.ended or process_match.stop_requested or process_match.match_count == process_match.total_to_match:
                    print("Matches done")
                    st.session_state["matching_in_progress"] = False
                    st.session_state["matching_done"] = True
else:
    progress_bar.empty()
    progress_text.empty()

# Display matching results if matching is done
if "matching_done" in st.session_state and st.session_state["matching_done"]:
    process_match = st.session_state["process_match"]
    vendas_ids = list(process_match.matched_vendas.keys())

    rents = list(process_match.matched_rent.values())

    df_rents = pd.DataFrame(rents, columns=['Rentabilidade'])
    fig = px.histogram(df_rents, x='Rentabilidade', nbins=80, marginal="box", title='Distribuição das Rentabilidades')
    fig.update_layout(xaxis_title='Rentabilidade', yaxis_title='Frequência')
    st.plotly_chart(fig)

    st.write("Rentabilidade média: ", sum(rents) / len(rents))

    selected_venda = st.selectbox("Selecione uma venda para ver os casamentos:", vendas_ids)


    if st.button("Mostrar Casamentos para Venda Selecionada"):
        matched_df = process_match.get_venda_matches(process_match.matched_vendas[selected_venda])
        avg_rent = process_match.matched_rent[selected_venda] * 100
        st.metric(label="Average Rent", value=f"{avg_rent:.2f}%", delta="-" + str(abs(100 - avg_rent)) + "% from expected")
        st.dataframe(matched_df)
else:
    # Display initial message if files are not uploaded
    st.title("MatchTune")
    if file_compras is not None:
        st.write("Tabela de compras carregada.")
    else:
        st.write("Aguardando carregamento do arquivo de compras.")

    if file_vendas is not None:
        st.write("Tabela de vendas carregada.")
    else:
        st.write("Aguardando carregamento do arquivo de vendas.")
