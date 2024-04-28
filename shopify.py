from openai import OpenAI
import pandas as pd
import requests
import os
import threading
import json

client = OpenAI()


def call_openai(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content


output_df = pd.DataFrame(columns=['URL Slug', 'Meta Title', 'Description', 'Blog Content', 'Featured Image'])
output_lock = threading.Lock()

# Shopify API credentials
api_key = os.environ.get('SHOPIFY_API_KEY')
password = os.environ.get('SHOPIFY_ADMIN_TOKEN')
store_admin = os.environ.get('STORE_ADMIN')
blog_id = os.environ.get("SHOPIFY_BLOG_ID")
author = os.environ.get("AUTHOR_NAME")

# Headers for the request
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

def create_shopify_post(payload):
    response = requests.post(f"https://{store_admin}.myshopify.com/admin/api/2024-04/blogs/{blog_id}/articles.json",
    headers=headers,
    data=json.dumps(payload),
    auth=(api_key, password)
)
    if response.status_code == 201:
        print(f"Successfully created post with ID: {response.json()['article']['id']}")
    else:
        print(f"Error creating post: {response.content}")
        response.raise_for_status()  # This will raise an exception if the request failed


def generate_blog_post():
    try:
        url_slug = "dress-codes"
        meta_title = "A summary of all dress codes for Men"
        description = "All the different dress codes for men"
        system_prompt1 = "You are an essay-writing assistant who creates detailed outlines for essays. You always write at least 15 points for each outline."
        user_prompt1 = f"Create an outline for an essay about {meta_title} with at least 15 titles."

        print(f"Generating outline for URL Slug {url_slug}")
        essay_outline = call_openai(system_prompt1, user_prompt1)

        system_prompt2 = f'Internal links are VITAL for  SEO. Please always use 5 internal links. Never mention essay. Write an article using the {essay_outline}. Internal links are vital to SEO. Please always include a maximum 5 ahref internal links contextually in the article not just at the end. NEVER USE PLACEHOLDERS. ALWAYS WRITE ALL THE ARTICLE IN FULL. Always include 5 internal links. Output in HTML. Write an article using {essay_outline} with 3 paragraphs per heading. Each heading of the essay should have at least one list or table (with a small black border, and border between the rows and columns) also. It will go onto shopify so I dont need opening HTML tags. Create relative links using the following relative links contextually thoughout the article. Use a maximum of 3. /suit-basics/, /suit-fit/, /how-to-wear-a-suit/, /how-to-measure/, /dress-pants-fit/, /suit-cuts/, /suit-vs-tuxedo/, /how-to-wear-a-tuxedo/, /blue-tuxedo/, /tuxedo-shirt/, /best-affordable-tuxedos/, /formal-attire/, /wedding-attire/, /black-tie/, /business-professional/, /job-interview/, /smart-casual/, /business-casual/, /funeral-attire/, /suit-color/, /color-combinations/, /blazer-trousers/, /dress-shirt-fit/, /how-to-wear-a-dress-shirt/'
        user_prompt2 = f"Never leave an article incomplete, always write the entire thing. Make sure all content is relevant to the article. Use a fun tone of voice. Always include at least 5 internal links. Each heading from the essay outline should have at least 3 paragraphs and a table or list After writing the article, under H2 and H3 headers create an FAQ section, followed by FAQPage schema opening and closing with <script> tags."
        print("Types: ", type(system_prompt2), type(user_prompt2))
        print(f"Generating blog content for URL Slug {url_slug}")
        blog_content = call_openai(system_prompt2, user_prompt2)
        print(f"Generated blog content for URL Slug {url_slug}")
        result = {'URL Slug': url_slug, 'Meta Title': meta_title, 'Description': description, 'Blog Content': blog_content}
        with output_lock:
            global output_df
            output_df = pd.concat([output_df, pd.DataFrame([result])], ignore_index=True)
            output_df.to_csv('output.csv', index=False)
            print(f"Saved blog post for URL Slug {url_slug} to output.csv")

        # Prepare the payload for the Shopify API
        payload = {
            "article": {
                "title": meta_title,
                "author": author,
                "tags": "Blog Post, OpenAI",
                "body_html": blog_content
            }
        }

        # Send the POST request to the Shopify API
        print(f"Creating Shopify post for URL Slug {url_slug}")
        create_shopify_post(payload)

    except Exception as e:
        print(f"Error generating blog post for URL Slug {url_slug}: {e}")
        return None

if __name__ == "__main__":
    # main()
    generate_blog_post()

