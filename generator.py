from openai import OpenAI
import os

client = OpenAI()


def call_openai(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}
        ]
    )
    return response


def generate_article_ideas(prompt, n=5):
    # Generating multiple ideas from a single prompt
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are an assistant, helpful in generating article ideas. Respond with concise ideas, where each idea is separated in a single line."},
            {"role": "user", "content": "Generate {} article ideas about: {}".format(n, prompt)}
        ]
    )
    all_options = response.choices[0].message.content
    as_array = all_options.split("\n")
    filter_blanks = list(filter(lambda x: x != '', as_array))
    return filter_blanks


def generate_full_article(idea):
    # Generating a full article for each idea
    response = call_openai("You are an intelligent writer, able to take an idea and construct a full article", "Generate an article about: " + idea)
    extracted_article = response.choices[0].message.content
    return extracted_article


def save_articles_to_file(articles):
    # Create a folder
    folder_path = "articles"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Saving generated articles to a text file
    for i, article in enumerate(articles):
        with open("articles/article{}.txt".format(i+1), 'w') as file:
            file.write(article)


def main():
    prompt = input("Enter your prompt for article ideas: ")
    number_of_articles = int(input("Enter number of articles you would like to generate: "))
    ideas = generate_article_ideas(prompt, number_of_articles)

    articles = []
    for idea in ideas:
        print(f"Generating article for idea: {idea}")
        article = generate_full_article(idea)
        articles.append(article)

    save_articles_to_file(articles)
    print(f"Articles have been saved to articles/.")


if __name__ == "__main__":
    main()
