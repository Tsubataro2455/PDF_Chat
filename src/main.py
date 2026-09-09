import logging
import time

import streamlit as st
import voyageai
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_classic.chains import RetrievalQA
from langchain_voyageai import VoyageAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from voyageai.error import RateLimitError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


QDRANT_PATH = "./local_qdrant"
COLLECTION_NAME = "my_collection"
EMB_MODEL = 'voyage-4-lite'
vo = voyageai.Client()  # 環境変数 VOYAGE_API_KEY を使用


def init_pages():
    st.set_page_config(
        page_title="Ask My PDF(s)",
        page_icon="📑"
    )
    st.sidebar.title("Nav")


def select_model():
    model = st.sidebar.radio("Choose a model:", ("claude-haiku-4-5", "claude-sonnet-4-5"))
    if model == "claude-haiku-4-5":
        return ChatAnthropic(model='claude-haiku-4-5')
    elif model == "claude-sonnet-4-5":
        return ChatAnthropic(model='claude-sonnet-4-5')
    return ChatAnthropic(model=model, temperature=0)


def load_qdrant():
    # ベクトルDBの保存場所を定義
    client = QdrantClient(path=QDRANT_PATH)

    # すべてのコレクション名を取得
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]

    # コレクションが存在しなければ作成
    if COLLECTION_NAME not in collection_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
        logger.info("collection created")

    return QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=VoyageAIEmbeddings(model=EMB_MODEL)
    )


def check_token_counts(pdf_text):
    """埋め込み前のトークン数をログにのみ出力(APIレート制限にはカウントされない)"""
    total = 0
    for i, chunk in enumerate(pdf_text):
        n_tokens = vo.count_tokens([chunk], model=EMB_MODEL)
        total += n_tokens
        logger.info(f"チャンク{i+1}: {n_tokens} トークン")
    logger.info(f"合計: {total} トークン")
    return total


def build_vector_store(pdf_text):
    """テキストのEmbedding化 + ベクトルDBへの保存(無料枠のレート制限対応)"""
    check_token_counts(pdf_text)  # ログ出力のみ、画面には出さない

    qdrant = load_qdrant()

    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(pdf_text)

    for i, chunk in enumerate(pdf_text):
        for attempt in range(5):
            try:
                qdrant.add_texts([chunk])  # 1件ずつ送信(3RPM対応)
                break
            except RateLimitError:
                wait = 20 * (attempt + 1)
                logger.warning(f"レート制限発生({i+1}/{total}, 試行{attempt+1}回目)。{wait}秒待機します。")
                status_text.text(f"レート制限中... {wait}秒待機します ({i+1}/{total})")
                time.sleep(wait)
        else:
            logger.error(f"チャンク {i+1} の埋め込みに失敗しました。スキップします。")
            st.error(f"チャンク {i+1} の埋め込みに失敗しました。スキップします。")
            continue

        status_text.text(f"埋め込み中... {i+1}/{total}")
        progress_bar.progress((i + 1) / total)
        time.sleep(21)  # 3RPM = 20秒に1回のペースを守る

    status_text.text("完了しました!")
    logger.info("埋め込み処理が完了しました")


def build_qa_model(llm):
    qdrant = load_qdrant()
    retriever = qdrant.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 10}
    )
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        verbose=True
    )


def page_pdf_upload_and_build_vector_db():
    """PDFのアップロードページを作成"""
    st.title("PDF Upload")
    container = st.container()
    with container:
        pdf_text = get_pdf_text()
        if pdf_text:
            with st.spinner("Loading PDF ..."):
                build_vector_store(pdf_text)


def page_ask_my_pdf():
    # AIアシスタントにpdfの内容について質問するページの実装
    st.title("Ask My PDF(s)")

    llm = select_model()
    container = st.container()
    res_container = st.container()

    with container:
        query = st.text_input("Query: ", key="input")
        if not query:
            answer = None
        else:
            qa = build_qa_model(llm)
            if qa:
                with res_container:
                    result = qa.invoke({"query": query})
                    answer = result["result"]
            else:
                answer = None
        if answer:
            with res_container:
                st.markdown("## Answer")
                st.write(answer)


def get_pdf_text():
    uploaded_file = st.file_uploader(
        label='Upload your PDF file',
        type='pdf'
    )
    if uploaded_file:
        pdf_reader = PdfReader(uploaded_file)
        text = '\n\n'.join([page.extract_text() for page in pdf_reader.pages])
        # 大きなテキストを、検索に適したサイズのチャンクに分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        return text_splitter.split_text(text)
    else:
        return None


def main():
    init_pages()

    # モードの選択
    selection = st.sidebar.radio("Go to", ["PDF Upload", "Ask My PDF(s)"])
    if selection == "PDF Upload":
        page_pdf_upload_and_build_vector_db()
    elif selection == "Ask My PDF(s)":
        page_ask_my_pdf()


if __name__ == "__main__":
    main()