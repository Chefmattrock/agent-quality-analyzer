#!/usr/bin/env python3
import argparse
import asyncio
import sys
import json
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def get_page_source(url, wait_until='networkidle', timeout=30000, 
                         wait_for_selector=None, screenshot=None, 
                         user_agent=None, viewport=None, headers=None,
                         basic_auth=None, wait_time=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        context_options = {}
        if user_agent:
            context_options['user_agent'] = user_agent
        if viewport:
            context_options['viewport'] = viewport
        if headers:
            context_options['extra_http_headers'] = headers
        if basic_auth:
            context_options['http_credentials'] = basic_auth
            
        context = await browser.new_context(**context_options)
        page = await context.new_page()
        
        try:
            response = await page.goto(url, wait_until=wait_until, timeout=timeout)
            
            if response is None:
                raise Exception("Failed to navigate to URL")
            
            if response.status >= 400:
                raise Exception(f"HTTP {response.status} error: {response.status_text}")
            
            if wait_for_selector:
                try:
                    await page.wait_for_selector(wait_for_selector, timeout=timeout)
                except PlaywrightTimeoutError:
                    raise Exception(f"Timeout waiting for selector: {wait_for_selector}")
            
            if wait_time:
                await page.wait_for_timeout(wait_time)
            
            if screenshot:
                await page.screenshot(path=screenshot, full_page=True)
            
            html_content = await page.content()
            
            await context.close()
            await browser.close()
            return html_content
            
        except Exception as e:
            await context.close()
            await browser.close()
            raise e


def main():
    parser = argparse.ArgumentParser(description='Get full webpage source after JavaScript execution')
    parser.add_argument('url', help='URL to fetch')
    parser.add_argument('--wait-until', 
                        choices=['load', 'domcontentloaded', 'networkidle', 'commit'],
                        default='networkidle',
                        help='When to consider the page loaded (default: networkidle)')
    parser.add_argument('--timeout', 
                        type=int, 
                        default=30000,
                        help='Timeout in milliseconds (default: 30000)')
    parser.add_argument('--wait-for-selector',
                        help='Wait for a specific CSS selector to appear')
    parser.add_argument('--wait-time',
                        type=int,
                        help='Additional wait time in milliseconds after page load')
    parser.add_argument('--output', '-o',
                        help='Save output to file instead of printing')
    parser.add_argument('--screenshot',
                        help='Save a screenshot to the specified file')
    parser.add_argument('--user-agent',
                        help='Custom user agent string')
    parser.add_argument('--viewport',
                        help='Viewport size as "width,height" (e.g., "1920,1080")')
    parser.add_argument('--headers',
                        help='Extra HTTP headers as JSON string')
    parser.add_argument('--basic-auth',
                        help='Basic auth as "username:password"')
    
    args = parser.parse_args()
    
    try:
        viewport = None
        if args.viewport:
            width, height = map(int, args.viewport.split(','))
            viewport = {'width': width, 'height': height}
        
        headers = None
        if args.headers:
            headers = json.loads(args.headers)
        
        basic_auth = None
        if args.basic_auth:
            username, password = args.basic_auth.split(':', 1)
            basic_auth = {'username': username, 'password': password}
        
        html_content = asyncio.run(get_page_source(
            args.url,
            wait_until=args.wait_until,
            timeout=args.timeout,
            wait_for_selector=args.wait_for_selector,
            screenshot=args.screenshot,
            user_agent=args.user_agent,
            viewport=viewport,
            headers=headers,
            basic_auth=basic_auth,
            wait_time=args.wait_time
        ))
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Page source saved to: {args.output}")
            if args.screenshot:
                print(f"Screenshot saved to: {args.screenshot}")
        else:
            print(html_content)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()