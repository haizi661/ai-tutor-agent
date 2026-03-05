from ...core.events import AgentEvent
from ...core.ports import AnswerProvider, EventSink, UserAbortError


class CliEventSink(EventSink):
    def emit(self, event: AgentEvent) -> None:
        if event.type == "node.start" and event.source == "tutor":
            print("\n" + "=" * 50)
            print("👨‍🏫 [伴学智能体]: ", end="", flush=True)
            return

        if event.type == "node.stream" and event.source == "tutor":
            print(event.data.get("text", ""), end="", flush=True)
            return

        if event.type == "node.complete" and event.source == "tutor":
            print("\n")
            return

        if event.type == "node.start" and event.source == "tester":
            print("-" * 50)
            print("📝 [考核智能体]: 正在为您定制考题...\n")
            print("📝 测试题：", end="", flush=True)
            return

        if event.type == "node.stream" and event.source == "tester":
            print(event.data.get("text", ""), end="", flush=True)
            return

        if event.type == "node.complete" and event.source == "tester":
            print("\n")
            return

        # New Assessment Feature Events
        if event.type == "node.start" and event.source == "assessment_generator":
            print("-" * 50)
            print("🧠 [评估智能体]: 正在根据您的主题生成专属测评量表...\n")
            return

        if event.type == "assessment.question":
            if event.message:
                print("\n" + event.message)
            return

        if event.type == "node.start" and event.source == "user_profiler":
            print("-" * 50)
            print("📊 [分析智能体]: ", end="", flush=True)
            return

        if event.type == "node.stream" and event.source == "user_profiler":
            print(event.data.get("text", ""), end="", flush=True)
            return
            
        if event.type == "node.complete" and event.source == "user_profiler":
            print("\n")
            return

        if event.type == "node.start" and event.source == "evaluator":
            print("-" * 50)
            print("🧐 [评价智能体]: 正在进行多维度严格阅卷...\n")
            return

        if event.type == "assessment.result":
            total_score = event.data.get("total_score")
            logic_score = event.data.get("logic_score")
            concept_score = event.data.get("concept_score")
            feedback = event.data.get("feedback", "")
            print(
                f"📊 提取成绩 -> 总分: {total_score} | 逻辑推演: {logic_score} | 概念理解: {concept_score}"
            )
            print(f"💡 诊断: {feedback}")
            return

        if event.type == "session.warning":
            print(f"⚠️ 警告: {event.message or ''}")
            return

        if event.type == "route.decision":
            decision = event.data.get("decision")
            if decision == "pass":
                print("\n✅ 恭喜！逻辑严密，通过考核！本次闭环学习结束。")
            else:
                print("\n❌ 掌握不牢固，触发动态干预，打回重学！")
            return

        if event.type == "session.info" and event.message:
            print(event.message)


class CliAnswerProvider(AnswerProvider):
    def get_answer(self, prompt: str, *, state=None) -> str:
        del state
        user_input = input(prompt).strip()
        if user_input.lower() == "quit":
            raise UserAbortError("主动结束本次学习进程。")
        return user_input
