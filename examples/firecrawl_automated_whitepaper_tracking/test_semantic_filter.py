from semantic_filter import belongs_to_category
from category_prompt import DESIRED_CATEGORY

def test_belongs_to_category():
    """
    This test ensures that belongs_to_category returns a boolean indicating if the paper 
    likely belongs to the specified category, based on the model's classification.
    Also prints confidence scores for analysis.
    """

    # Our test cases with inputs and expected outputs
    test_cases = [
        (
            "PaliGemma 2: A Family of Versatile VLMs for Transfer",
            """PaliGemma 2 is an upgrade of the PaliGemma open Vision-Language Model (VLM) based on the Gemma 2 family of language models. We combine the SigLIP-So400m vision encoder that was also used by PaliGemma with the whole range of Gemma 2 models, from the 2B one all the way up to the 27B model. We train these models at three resolutions (224px, 448px, and 896px) in multiple stages to equip them with broad knowledge for transfer via fine-tuning. The resulting family of base models covering different model sizes and resolutions allows us to investigate factors impacting transfer performance (such as learning rate) and to analyze the interplay between the type of task, model size, and resolution. We further increase the number and breadth of transfer tasks beyond the scope of PaliGemma including different OCR-related tasks such as table structure recognition, molecular structure recognition, music score recognition, as well as long fine-grained captioning and radiography report generation, on which PaliGemma 2 obtains state-of-the-art results.""",
            DESIRED_CATEGORY,
            False
        ),
        (
            "From Generation to Judgment: Opportunities and Challenges of LLM-as-a-judge",
            """Assessment and evaluation have long been critical challenges in artificial intelligence (AI) and natural language processing (NLP). However, traditional methods, whether matching-based or embedding-based, often fall short of judging subtle attributes and delivering satisfactory results. Recent advancements in Large Language Models (LLMs) inspire the "LLM-as-a-judge" paradigm, where LLMs are leveraged to perform scoring, ranking, or selection across various tasks and applications. This paper provides a comprehensive survey of LLM-based judgment and assessment, offering an in-depth overview to advance this emerging field. We begin by giving detailed definitions from both input and output perspectives. Then we introduce a comprehensive taxonomy to explore LLM-as-a-judge from three dimensions: what to judge, how to judge and where to judge. Finally, we compile benchmarks for evaluating LLM-as-a-judge and highlight key challenges and promising directions, aiming to provide valuable insights and inspire future research in this promising research area. Paper list and more resources about LLM-as-a-judge can be found at https://github.com/llm-as-a-judge/Awesome-LLM-as-a-judge and https://llm-as-a-judge.github.io.""",
            DESIRED_CATEGORY,
            False
        ),
        (
            "Evaluation Agent: Efficient and Promptable Evaluation Framework for Visual Generative Models",
            """Recent advancements in visual generative models have enabled high-quality image and video generation, opening diverse applications. However, evaluating these models often demands sampling hundreds or thousands of images or videos, making the process computationally expensive, especially for diffusion-based models with inherently slow sampling. Moreover, existing evaluation methods rely on rigid pipelines that overlook specific user needs and provide numerical results without clear explanations. In contrast, humans can quickly form impressions of a model's capabilities by observing only a few samples. To mimic this, we propose the Evaluation Agent framework, which employs human-like strategies for efficient, dynamic, multi-round evaluations using only a few samples per round, while offering detailed, user-tailored analyses. It offers four key advantages: 1) efficiency, 2) promptable evaluation tailored to diverse user needs, 3) explainability beyond single numerical scores, and 4) scalability across various models and tools. Experiments show that Evaluation Agent reduces evaluation time to 10% of traditional methods while delivering comparable results. The Evaluation Agent framework is fully open-sourced to advance research in visual generative models and their efficient evaluation.""",
            DESIRED_CATEGORY,
            True
        ),
        (
            "TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks",
            """We interact with computers on an everyday basis, be it in everyday life or work, and many aspects of work can be done entirely with access to a computer and the Internet. At the same time, thanks to improvements in large language models (LLMs), there has also been a rapid development in AI agents that interact with and affect change in their surrounding environments. But how performant are AI agents at helping to accelerate or even autonomously perform work-related tasks? The answer to this question has important implications for both industry looking to adopt AI into their workflows, and for economic policy to understand the effects that adoption of AI may have on the labor market. To measure the progress of these LLM agents' performance on performing real-world professional tasks, in this paper, we introduce TheAgentCompany, an extensible benchmark for evaluating AI agents that interact with the world in similar ways to those of a digital worker: by browsing the Web, writing code, running programs, and communicating with other coworkers. We build a self-contained environment with internal web sites and data that mimics a small software company environment, and create a variety of tasks that may be performed by workers in such a company. We test baseline agents powered by both closed API-based and open-weights language models (LMs), and find that with the most competitive agent, 24% of the tasks can be completed autonomously. This paints a nuanced picture on task automation with LM agents -- in a setting simulating a real workplace, a good portion of simpler tasks could be solved autonomously, but more difficult long-horizon tasks are still beyond the reach of current systems.""",
            DESIRED_CATEGORY,
            True
        ),
        (
            "GUI Agents: A Survey",
            """Graphical User Interface (GUI) agents, powered by Large Foundation Models, have emerged as a transformative approach to automating human-computer interaction. These agents autonomously interact with digital systems or software applications via GUIs, emulating human actions such as clicking, typing, and navigating visual elements across diverse platforms. Motivated by the growing interest and fundamental importance of GUI agents, we provide a comprehensive survey that categorizes their benchmarks, evaluation metrics, architectures, and training methods. We propose a unified framework that delineates their perception, reasoning, planning, and acting capabilities. Furthermore, we identify important open challenges and discuss key future directions. Finally, this work serves as a basis for practitioners and researchers to gain an intuitive understanding of current progress, techniques, benchmarks, and critical open problems that remain to be addressed.""",
            DESIRED_CATEGORY,
            True
        ),
        (
            "Aguvis: Unified Pure Vision Agents for Autonomous GUI Interaction",
            """Graphical User Interfaces (GUIs) are critical to human-computer interaction, yet automating GUI tasks remains challenging due to the complexity and variability of visual environments. Existing approaches often rely on textual representations of GUIs, which introduce limitations in generalization, efficiency, and scalability. In this paper, we introduce Aguvis, a unified pure vision-based framework for autonomous GUI agents that operates across various platforms. Our approach leverages image-based observations, and grounding instructions in natural language to visual elements, and employs a consistent action space to ensure cross-platform generalization. To address the limitations of previous work, we integrate explicit planning and reasoning within the model, enhancing its ability to autonomously navigate and interact with complex digital environments. We construct a large-scale dataset of GUI agent trajectories, incorporating multimodal reasoning and grounding, and employ a two-stage training pipeline that first focuses on general GUI grounding, followed by planning and reasoning. Through comprehensive experiments, we demonstrate that Aguvis surpasses previous state-of-the-art methods in both offline and real-world online scenarios, achieving, to our knowledge, the first fully autonomous pure vision GUI agent capable of performing tasks independently without collaboration with external closed-source models. We open-sourced all datasets, models, and training recipes to facilitate future research at https://aguvis-project.github.io/.""",
            DESIRED_CATEGORY,
            True
        ),
    ]

    # Track failed tests
    failed_tests = []

    # Run each test case
    for paper_title, paper_abstract, desired_category, expected_boolean in test_cases:
        try:
            # Get the raw response from the model
            result, confidence = belongs_to_category(paper_title, paper_abstract, desired_category)
            
            # Print the confidence score and classification result
            print(f"\nPaper: {paper_title[:50]}...")
            print(f"Expected category match: {expected_boolean}")
            print(f"Actual category match: {result}")
            print(f"Confidence score: {confidence:.2f}")
            
            assert isinstance(result, bool), "The result should be a boolean."
            if result != expected_boolean:
                failed_tests.append({
                    'title': paper_title[:50],
                    'expected': expected_boolean,
                    'got': result
                })
                
        except Exception as e:
            failed_tests.append({
                'title': paper_title[:50],
                'error': str(e)
            })

    # Print summary at the end
    print("\n=== Test Summary ===")
    if not failed_tests:
        print("All tests passed successfully!")
    else:
        print(f"Failed tests ({len(failed_tests)}):")
        for test in failed_tests:
            if 'error' in test:
                print(f"- {test['title']}: {test['error']}")
            else:
                print(f"- {test['title']}: expected {test['expected']}, got {test['got']}")
        raise AssertionError("Some tests failed. See summary above.")

if __name__ == "__main__":
    test_belongs_to_category()
