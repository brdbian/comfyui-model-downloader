try:
    import comfy.model_management as model_management

    InterruptProcessingException = model_management.InterruptProcessingException
except ImportError:
    model_management = None
    InterruptProcessingException = None


def throw_if_interrupted():
    if model_management is not None:
        model_management.throw_exception_if_processing_interrupted()


def is_interrupted() -> bool:
    if model_management is not None:
        return model_management.processing_interrupted()
    return False
