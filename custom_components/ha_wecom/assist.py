import logging
from homeassistant.core import Context
from homeassistant.util.ulid import ulid_now

_LOGGER = logging.getLogger(__name__)

# 优先使用 HA 2025/2026 的 Assist Pipeline 新架构；
# 老版本 HA 不存在这些类/字段时，回退到 conversation.async_converse。
try:
    from homeassistant.helpers.chat_session import ChatSession
    from homeassistant.components.assist_pipeline.pipeline import (
        async_get_pipeline,
        PipelineRun,
        PipelineStage,
        PipelineInput,
        PipelineEvent,
        PipelineEventType,
    )
    _USE_PIPELINE = True
except (ImportError, AttributeError):  # pragma: no cover - 老版本 HA
    from homeassistant.components import conversation
    _USE_PIPELINE = False


async def async_assistant(hass, text):
    """通过本地默认语音助手处理文本，返回自然语言回复。

    兼容策略：
    - 新版本 HA：使用 Assist Pipeline 事件回调方式处理；
    - 老版本 HA（无 PipelineInput 等新 API）：回退到 conversation.async_converse。
    """
    if _USE_PIPELINE:
        return await _run_pipeline(hass, text)
    return await _run_converse(hass, text)


async def _run_pipeline(hass, text):
    """HA 2025/2026：通过首选 Assist 管道（语音助手）处理文本。"""
    try:
        # pipeline_id=None 时返回当前首选管道
        pipeline = async_get_pipeline(hass)
    except Exception as ex:
        _LOGGER.error('获取首选 Assist 管道失败: %s', ex)
        return None

    result: dict = {}

    def event_callback(event: PipelineEvent) -> None:
        if event.type == PipelineEventType.INTENT_END:
            intent_output = (event.data or {}).get('intent_output')
            if intent_output:
                speech = (
                    intent_output.get('response', {})
                    .get('speech', {})
                    .get('plain', {})
                    .get('speech')
                )
                result['text'] = speech

    run = PipelineRun(
        hass=hass,
        context=Context(),
        pipeline=pipeline,
        start_stage=PipelineStage.INTENT,
        end_stage=PipelineStage.INTENT,
        event_callback=event_callback,
    )
    pipeline_input = PipelineInput(
        run=run,
        session=ChatSession(conversation_id=ulid_now()),
        intent_input=text,
    )

    try:
        await pipeline_input.execute(validate=True)
    except Exception as ex:
        _LOGGER.error('运行 Assist 管道失败: %s', ex)
        return None

    return result.get('text')


async def _run_converse(hass, text):
    """回退路径：直接调用默认的 conversation 语音助手。"""
    try:
        result = await conversation.async_converse(
            hass, text, None, Context(), None, None, None
        )
    except Exception as ex:
        _LOGGER.error('调用默认语音助手失败: %s', ex)
        return None

    try:
        return result.response.speech.get('plain').speech
    except AttributeError:
        return None
