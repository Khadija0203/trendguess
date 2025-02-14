import streamlit as st
import os
import time
 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from serpapi import GoogleSearch
 
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
 
MODEL_ID = "gemini-2.0-flash"
 
@st.cache_resource
def get_model():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash")
 
 
@st.cache_data  # top pour faire appel a notre API pour ne pas avoir à le rappeler à chaque fois
def call_api():
    params = {
        "engine": "google_trends_trending_now",
        "geo": "FR",
        "api_key": "", # Remplacer par votre cle
        "hours": "168"
    }
 
    search = GoogleSearch(params)
    results = search.get_dict()
 
    trending_searches = results.get("trending_searches", [])
 
    # On filtre selon:
    datas = [
        {
            "query": item["query"],
            "category": item["categories"][0]["name"],
            "search_volume": item["search_volume"]
        }
        for item in trending_searches
        if item["categories"] and "name" in item["categories"][0] and item["categories"][0]["name"] in ["Sports", "Climate"]
    ]
    return datas
 
 
st.title("Trend Guess")
 
model = get_model()
 
datas = call_api()
 
@st.cache_data
def get_hint(position):
    sujet = datas[position]["query"]
    question = ChatPromptTemplate.from_messages(
        [
            ("system", """Tu es le maître d'un jeu de devinettes. Ton rôle est de proposer trois indices pertinents mais sans trop en révéler, pour que le joueur puisse deviner la réponse.
 
            Si l'exemple est : Manchester City - Real Madrid
            Voici les indices types que tu pourrais donner:
            1. Ce match oppose un club de Premier League à une équipe légendaire de Liga.
            2. L'un des deux clubs détient le record du plus grand nombre de victoires en Ligue des champions.
            3. Des joueurs emblématiques comme Cristiano Ronaldo et David Beckham ont évolué dans les deux camps.
 
            Si l'exemple est: Tremblement de terre maroc
            Voici les indices types que tu pourrais donner:
            1. Cet événement est une secousse soudaine et puissante du sol, pouvant causer des destructions.
            2. Il s'est produit dans un pays connu pour sa culture riche, ses villes historiques et la chaîne de l’Atlas.
            3. Ce drame a frappé un pays en septembre 2023, causant de nombreux dégâts et pertes humaines.
 
            Instructions :
            - Débutes comme dans un jeu
            - Attention! Ne donne pas le sujet à déviner en donnant les indices.
            - Les indices doivent être clairs mais légèrement mystérieux.
            - Évite de donner la réponse directement.
            - Rends le jeu amusant et engageant. Evite de répéter la meme chose à l'utilisateur et varie tes réponses.
 
            """),
            ("user", "{sujet}")
        ]
    )
    prompt = question.invoke({"sujet": sujet})
    response = model.invoke(prompt)
    return {"role": "assistant", "content": response.content}
def check_response(position):
    sujet = datas[position]["query"]
    response_check = ChatPromptTemplate.from_messages(
        [
            ("system", """Tu es le maître d'un jeu de devinettes. Ton rôle est de proposer trois indices pertinents mais sans trop en révéler, pour que le joueur puisse deviner la réponse.
 
            Tu es le maître d'un jeu de devinettes. Ton rôle est de vérifier si la réponse donnée est correcte.
 
        La vraie réponse est "{sujet}"
        Il a deviné et trouvé "{prompts}". Est-ce acceptable comme réponse ?
 
        Instructions:
        - "{prompts}" doit être très proche de "{sujet}" et complet pour un succès.
        - Si c'est le cas, félicite-le, précise lui la vraie réponse et annonce qu'il le prochain sujet sans donner de précision à propos.
        - Si non, juge sa réponse sur un ton ironnique et  donne-lui le bon résultat et demandes lui de suivre plus souvent l'actualité sur un ton irronique.
        - Rends le jeu amusant et engageant. Evite de répéter la meme chose à l'utilisateur et varie tes réponses.
 
            """),
            ("user", "{prompts}")
        ]
    )
    prompt_check = response_check.invoke({"prompts": prompts,"sujet": sujet})
    response = model.invoke(prompt_check)
    return {"role": "assistant", "content": response.content}
 
if 'count' not in st.session_state:
    st.session_state['count'] = 0
 
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        get_hint(1)
    ]
 
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
 
# Accept user input
if prompts := st.chat_input("C'est ton tour"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompts)
    st.session_state.messages.append({"role": "user", "content": prompts})
    st.session_state.messages = [
        check_response(1)
    ]
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
 