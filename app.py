import asyncio
import streamlit as st
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
import re

# --- Streamlit page configuration ---
st.set_page_config(page_title="Multi-Agent | Requirements to Code Generator", layout="wide")

# Advanced Orchestrator class to manage multi-agent workflow
class Orchestrator:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

        self.requirements_agent = ChatCompletionAgent(
            service=self.kernel.get_service("openai-chat"),
            name="RequirementsAgent",
            instructions=(
                "You are an expert software analyst. "
                "Read the application requirements carefully and clarify or confirm understanding."
            )
        )

        self.user_story_agent = ChatCompletionAgent(
            service=self.kernel.get_service("openai-chat"),
            name="UserStoryAgent",
            instructions=(
                """
                    You are a skilled Product Owner.
                    Break down the application requirements into exactly 8 detailed user stories.
                    For each user story, write clear and concise acceptance criteria using the Given / When / Then format.
                    Number only the user stories (1–8). Do not number the individual acceptance criteria.
                    
                    User Story:
                    As a [type of user], I want to [perform some action], so that [I get some benefit].
                    Acceptance Criteria Format:
                    Given [some initial context],
                    When [an action is taken],
                    Then [expect a specific result].
                """
            )
        )

        self.code_gen_agent = ChatCompletionAgent(
            service=self.kernel.get_service("openai-chat"),
            name="CodeGenAgent",
            instructions=(
                "You are a senior Jquery developer. "
                "Generate clear, concise sample jquery code implementing the given user story."
            )
        )

        self.aggregator_agent = ChatCompletionAgent(
            service=self.kernel.get_service("openai-chat"),
            name="AggregatorAgent",
            instructions=(
                "You are a senior software engineer. Combine all the given Jquery code snippets "
                "into a single, complete, and logically structured code file. Remove redundancies and ensure "
                "it works as a coherent application. Do not add explanations — just return the final code."
            )
        )

    async def run(self, requirements: str):
        st.write("Sending requirements to RequirementsAgent...")
        requirements_response = await self.requirements_agent.get_response(
            messages=[ChatMessageContent(role="user", content=requirements)]
        )
        clarified_requirements = requirements_response.content.content.strip()
        st.subheader("Clarified Requirements")
        st.write(clarified_requirements)

        st.subheader("Breaking down requirements into user stories via UserStoryAgent...")
        user_stories_response = await self.user_story_agent.get_response(
            messages=[ChatMessageContent(role="user", content=requirements)]
        )
        user_stories_text = user_stories_response.content.content.strip()
        st.subheader("User Stories")
        user_stories = self._parse_user_stories(user_stories_text)
        for idx, story in enumerate(user_stories, start=1):
            st.write(f"{idx}: {story}")

        st.subheader("Generating sample code for each user story via CodeGenAgent...")
        code_snippets = {}
        st.subheader("Generated Code Snippets")
        for idx, story in enumerate(user_stories, start=1):
            st.write(f"Generating code for User Story {idx}: {story}")
            code_response = await self.code_gen_agent.get_response(
                messages=[ChatMessageContent(role="user", content=clarified_requirements)]
            )
            code_snippets[story] = code_response.content.content.strip()
            st.code(code_snippets[story], language="html")

        # Aggregate all generated code
        # Aggregate all generated code into a single file
        st.subheader("Aggregating all code snippets into one complete file via AggregatorAgent...")
       
        all_code_combined = "\n\n".join(code_snippets.values())
        aggregation_response = await self.aggregator_agent.get_response(
            messages=[ChatMessageContent(role="user", content=all_code_combined)]
        )
        final_combined_code = aggregation_response.content.content.strip()

        st.subheader("Final Combined Code File")
        st.code(final_combined_code, language="javascript")  # assuming jQuery/JS
        
        return {
            "clarified_requirements": clarified_requirements,
            "user_stories": user_stories,
            "code_snippets": code_snippets,
        }

    def _parse_user_stories(self, text: str):
        lines = text.splitlines()
        user_stories = []
        story_pattern = re.compile(r"^As a .*?, I want to .*?, so that .*", re.IGNORECASE)

        for line in lines:
            line = line.strip()
            if story_pattern.match(line):
                user_stories.append(line)
        return user_stories


async def main():
    # --- Sidebar with model information ---
    with st.sidebar:
        st.header("ℹ️ Agents Instructions")
        # Expandable section for Cohere Embed-4 model details
        with st.expander("Requirements Agent", expanded=True):
            st.markdown("""
            - You are an expert software analyst. 
            - Read the application requirements carefully and clarify or confirm understanding.
            """)
        # Expandable section for Google Gemini 2.5 Flash model details
        with st.expander("UserStory Agent", expanded=True):
            st.markdown("""
                    You are a skilled Product Owner.
                    Break down the application requirements into exactly 8 detailed user stories.
                    For each user story, write clear and concise acceptance criteria using the Given / When / Then format.
                    Number only the user stories (1–8). Do not number the individual acceptance criteria.
                    
                    User Story:
                    As a [type of user], I want to [perform some action], so that [I get some benefit].
                    Acceptance Criteria Format:
                    Given [some initial context],
                    When [an action is taken],
                    Then [expect a specific result].
            """)
        
        with st.expander("CodeGen Agent", expanded=True):
            st.markdown("""
            You are a senior Jquery developer. 
            Generate clear, concise sample jquery code implementing the given user story.
            """)
        
        with st.expander("Aggregator Agent", expanded=True):
            st.markdown("""
            - You are a senior software engineer. 
            - Combine all Jquery code snippets into a single working code file.
            - Ensure it's logically structured and functions as one application.
            """)
    st.title("Multi-Agent | Requirements to Code Generator")
    st.write("Provide your application requirements, Agents will generate clarified requirements, break those into user stories, and generate a sample code.")

    OPEN_AI_KEY = "skA"  # Replace with actual key
    MODEL_ID = "gpt-4"

    kernel = Kernel()

    # Register OpenAI chat service with correct service_id
    kernel.add_service(
        OpenAIChatCompletion(
            api_key=OPEN_AI_KEY,
            ai_model_id=MODEL_ID,
            service_id="openai-chat"
        )
    )

    orchestrator = Orchestrator(kernel)

    app_requirements = st.text_area(
        "Enter Application Requirements:",
        """Create a single-page registration form with a clean and modern theme. Include social login icons (e.g., Google, Facebook, GitHub) purely for visual purposes—no functionality required. The form should have an email input field that is required and includes proper email format validation.""",
        height=90,
        help="Describe the application requirements clearly. The agents will clarify and break them down into user stories."
    )

    if st.button("Generate"):
        with st.spinner("Processing..."):
            results = await orchestrator.run(app_requirements)

        st.subheader("Final Aggregated Results")
        st.write("### Clarified Requirements")
        st.write(results["clarified_requirements"])

        st.write("### User Stories")
        for idx, story in enumerate(results["user_stories"], start=1):
            st.write(f"{story}")

        st.write("### Generated Code Snippets")
        for idx, (story, code) in enumerate(results["code_snippets"].items(), start=1):
            st.write(f"**User Story {idx}:** {story}")
            st.code(code, language="html")


if __name__ == "__main__":
    asyncio.run(main())

