# The code is importing various modules and classes from different libraries. Here's a breakdown of
# the imports:
from llama_index.callbacks.base import CallbackManager
from llama_index import download_loader, LLMPredictor, PromptHelper, ServiceContext, StorageContext, load_index_from_storage
from langchain.chat_models import ChatOpenAI
from llama_hub.file.unstructured.base import UnstructuredReader
import chainlit as cl
import os
import openai

# This code block is responsible for setting up the necessary configurations and dependencies for the
# code to run. Here's a breakdown of what it does:
os.environ["OPENAI_API_KEY"] = input("Enter OpenAI API Key: ")
openai.api_key = os.environ["OPENAI_API_KEY"]


UnstructuredReader = download_loader('UnstructuredReader')


try:
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    # load index
    index = load_index_from_storage(storage_context)
except:
    from llama_index import VectorStoreIndex, SimpleDirectoryReader

    dir_reader = SimpleDirectoryReader("./data", file_extractor={
        ".txt": UnstructuredReader(),
        ".docx": UnstructuredReader(),
        ".pptx": UnstructuredReader(),
        ".pdf": UnstructuredReader(),
        ".jpg": UnstructuredReader(),
        ".png": UnstructuredReader(),
        ".eml": UnstructuredReader(),
        ".html": UnstructuredReader(),
    })

    documents = dir_reader.load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist()


@cl.on_chat_start
async def factory():
    llm_predictor = LLMPredictor(
        llm=ChatOpenAI(
            temperature=0,
            model_name="gpt-4",
            streaming=True,
        ),
    )
    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor,
        chunk_size=512,
        callback_manager=CallbackManager([cl.LlamaIndexCallbackHandler()]),
    )

    query_engine = index.as_query_engine(
        service_context=service_context,
        streaming=True,
    )

    cl.user_session.set("query_engine", query_engine)


@cl.on_message
async def main(message: cl.Message):
    query_engine = cl.user_session.get(
        "query_engine")
    response = await cl.make_async(query_engine.query)(message.content)

    response_message = cl.Message(content="")

    for token in response.response_gen:
        await response_message.stream_token(token=token)

    if response.response_txt:
        response_message.content = response.response_txt

    await response_message.send()


############################################ OLD CODE ############################################
# def construct_index(directory_path):
#     # set maximum input size
#     max_input_size = 4096
#     # set number of output tokens
#     num_outputs = 2000
#     # set maximum chunk overlap
#     max_chunk_overlap = 0.2
#     # set chunk size limit
#     chunk_size = 600

#     # define prompt helper
#     prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size)

#     # define LLM
#     llm_predictor = LLMPredictor(llm=ChatOpenAI(openai_api_key=openai.api_key, temperature=0.2, model_name="gpt-4", max_tokens=num_outputs))

#     dir_reader = SimpleDirectoryReader(directory_path, recursive=True, filename_as_id=True, file_extractor={
#       ".txt": UnstructuredReader(),
#       ".docx": UnstructuredReader(),
#       ".pptx": UnstructuredReader(),
#       ".pdf": UnstructuredReader(),
#       ".jpg": UnstructuredReader(),
#       ".png": UnstructuredReader(),
#       ".eml": UnstructuredReader(),
#       ".html": UnstructuredReader(),
#     })
#     documents = dir_reader.load_data()
#     print(f"Loaded {len(documents)} docs!")


#     service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)
#     index = VectorStoreIndex.from_documents(documents, service_context=service_context)

#     index.storage_context.persist()

#     return index


# # def ask_jarvis():
#     # rebuild storage context
#     storage_context = StorageContext.from_defaults(persist_dir="./storage")
#     # load index
#     index = load_index_from_storage(storage_context)
#     while True:
#         query_engine = index.as_query_engine()
#         query = input("Hello! What would you like to know?")
#         response = query_engine.query(query)
#         display(Markdown(f"Response: <b>{response.response}</b>"))


# construct_index("data")
# ask_jarvis()
