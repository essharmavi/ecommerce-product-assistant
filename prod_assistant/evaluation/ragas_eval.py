from ragas import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import LLMContextPrecisionWithoutReference, ResponseRelevancy
from grpc.experimental.aio import grpc_aio
from utils.model_loader import ModelLoader
import asyncio

grpc_aio.init_grpc_aio()
model_loader = ModelLoader()

def evaluation_context_precision(query, response, retrieved_context):

    try:
        sample = SingleTurnSample(
            query=query,
            response=response,
            context=retrieved_context
        )
        async def main():
            llm = ModelLoader().load_llm()
            evaluator_llm = LangchainLLMWrapper(llm)
            context_precision = LLMContextPrecisionWithoutReference(llm=evaluator_llm)
            result = await context_precision.single_turn_ascore(sample)
            return result
        
        return asyncio.run(main())
    except Exception as e:
        print(f"Error during context precision evaluation: {e}")
        return e



def evaluation_response_relevancy(query, response, retrieved_context):
    try:
        sample = SingleTurnSample(
            query=query,
            response=response,
            context=retrieved_context
        )
        async def main():
            llm = ModelLoader().load_llm()
            evaluator_llm = LangchainLLMWrapper(llm)
            scorer = ResponseRelevancy(llm=evaluator_llm)
            result = await scorer.single_turn_ascore(sample)
            return result
        
        return asyncio.run(main())
    except Exception as e:
        print(f"Error during context precision evaluation: {e}")
        return e




