from openai import OpenAI
import pandas as pd
import requests
import os
import threading
import json
from tqdm import tqdm
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

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
    # Shopify API reference: https://shopify.dev/docs/api/admin-rest/2024-04/resources/article
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


def generate_blog_post(row):
    url_slug = row['URL Slug']
    meta_title = row['Meta Title']
    description = row['Description of Page']

    try:
        system_prompt1 = "You are an essay-writing assistant who creates detailed outlines for essays. You always write at least 15 points for each outline."
        user_prompt1 = f"Create an outline for an essay about {meta_title} with at least 15 titles."

        essay_outline = call_openai(system_prompt1, user_prompt1)
        print("Essay outline is: ", essay_outline)

        system_prompt2 = f'Never mention essay. Write an article using the {essay_outline}. NEVER USE PLACEHOLDERS. ALWAYS WRITE ALL THE ARTICLE IN FULL. Output in HTML. Write an article using {essay_outline} with 3 paragraphs per heading. Each heading of the essay should have at least one list or table (with a small black border, and border between the rows and columns) also. It will go onto wordpress so I dont need opening HTML tags.'
        user_prompt2 = f"Never leave an article incomplete, always write the entire thing. Make sure all content is relevant to the article. Use a fun tone of voice. Each heading from the essay outline should have at least 3 paragraphs and a table or list."
        blog_content = call_openai(system_prompt2, user_prompt2)
        print("Blog content is: ", blog_content)
        result = {'URL Slug': url_slug, 'Meta Title': meta_title, 'Description': description,
                  'Blog Content': blog_content}
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


def main():
    df = pd.read_csv('keywords.csv')

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(generate_blog_post, row) for index, row in df.iterrows()]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            try:
                future.result()  # To raise exceptions if any occurred during the thread's execution
            except Exception as e:
                print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
