#!/usr/bin/env python
# coding: utf-8

# In[22]:


# pyton 3.7


# In[23]:


import requests
import pdftotext
import time
import io
import json
from bs4 import BeautifulSoup
from doccloud_secret import DOCUMENT_CLOUD_USER
from doccloud_secret import DOCUMENT_CLOUD_PASS
from documentcloud import DocumentCloud


# ### Typical Format
# 
# - Call Category
# - Location
# - Date Report
# - Case #
# - Date Occurred
# - Time Occurred
# - Summary
# - Dispotion
# - Arrest Info (if applicable) 

# In[24]:


project_id = "49471-ucsd-police-log-database"
crime_log_url_addr = "http://www.police.ucsd.edu/docs/reports/CallsandArrests/Calls_and_Arrests.asp"
crime_log_prefix = "http://www.police.ucsd.edu/docs/reports/CallsandArrests/"
data_fields = ["CALL_CATEGORY", "LOCATION", "DATE_REPORTED", "CASE_NUMBER",
               "DATE_OCCURRED", "TIME_OCCURRED", "SUMMARY", "DISPOSITION", "ARREST", "IS_UPDATE"]
doc_cloud_client = DocumentCloud(DOCUMENT_CLOUD_USER, DOCUMENT_CLOUD_PASS)


# In[25]:


project_docs = doc_cloud_client.projects.get(title="UCSD Police Log Database").document_list


# In[26]:


# splits the texts into sublists of their entries
def get_entries(page_text):
    entries_list = []
    entry        = []
    entry_delim  = [(i - 2) for i in range(0, len(page_text)) if page_text[i].startswith("Date Reported")]
    entry_delim.append(len(page_text))
    entries_list = [page_text[ele0:ele1] 
                        for (ele0, ele1) in zip(entry_delim[:-1], entry_delim[1:])] 
    return entries_list


# In[27]:


# separates each entries fields into a python dict
# entry_text_list – the entry split into a list split along each new line
# is_update       – whether the entry is from a log updating a previous log
# pdf_url         – the public documentcloud pdf upload of the entry's corresponding log
def parse_log_entry(entry_text_list, is_update, pdf_url):
    VAR_LEN_FIELD_PREFIXES = {"Summary": "SUMMARY", "Disposition": "DISPOSITION", "Arrest Date": "ARREST"}
    PREFIX_LIST            = list(VAR_LEN_FIELD_PREFIXES.keys()) + ["Date Reported", "Incident/Case#", 
                                                                    "Date Occurred", "Time Occurred "]
    LAST_FIXED_LEN_FIELD   = 6
    line_i = 0
    prefix = ""
    entry = dict()
    # get all entries that only take up 1 line
    for field in data_fields[0:LAST_FIXED_LEN_FIELD]:
        value = entry_text_list[line_i]
        prefix_filter = list(filter(entry_text_list[line_i].startswith, PREFIX_LIST))
        if(prefix_filter != []):
            value = value.strip(prefix_filter[0]).strip()
        entry[field] = value
        line_i+=1
    # get all entries that can take up multiple lines
    for line_i in range(line_i, len(entry_text_list)):
        prefix_filter = list(filter(entry_text_list[line_i].startswith, PREFIX_LIST))
        if(prefix_filter != []):
            prefix = prefix_filter[0]
        if(VAR_LEN_FIELD_PREFIXES[prefix] in entry):
            entry[VAR_LEN_FIELD_PREFIXES[prefix]] = entry[VAR_LEN_FIELD_PREFIXES[prefix]] + (entry_text_list[line_i].strip())
        else:
            entry[VAR_LEN_FIELD_PREFIXES[prefix]] = entry_text_list[line_i].lstrip(prefix).lstrip(':').lstrip()
    if("ARREST" in entry):
        entry["ARREST"] = True
    else:
        entry["ARREST"] = False
    entry["IS_UPDATE"] = is_update
    entry["PDF"] = pdf_url
    return entry


# In[28]:


# splits the pdf along new lines characters, determine whether it is an update and then get the pdf's corpus of entries
# pdf     – pdftotext object of the current log
# pdf_url – the public documentcloud pdf upload of the entry's corresponding log
def parse_log_pdf(pdf, pdf_url="#"):    
    DATE_LINE = 2 # index with the dateline in the header
    # iterate through the pages
    corpus = []
    for page in pdf:
        # split page into array of strings based on new line character
        page_text = page.split('\n')
        if ("UPDATE" in page_text[DATE_LINE]): # TODO: move this check earlier in the processing
            is_update = True
        else:
            is_update = False
        entries = get_entries(page_text)
        corpus = corpus + [parse_log_entry(entry, is_update, pdf_url) for entry in entries]
    return corpus


# In[43]:


def upload_pdf(url, title):
    document_titles = [doc for doc in project_docs if doc.title == title]
    if(len(document_titles) > 0):
        return document_titles[0].canonical_url
    
    document = doc_cloud_client.documents.upload(url, title, source=crime_log_url_addr, access="public",
                                                 project=project_id)
    pdf_url = document.canonical_url
    return pdf_url


# In[38]:


# parses the pdf and uploads it to document cloud
# url_day_suffic – the file's location on the UCPD server
def parse_daily_log(url_day_suffix):
    log_response = requests.get(crime_log_prefix + url_day_suffix)
    url = log_response.url
    raw_pdf_data = log_response.content
    
    with io.BytesIO(raw_pdf_data) as open_pdf_file:
        read_pdf = pdftotext.PDF(open_pdf_file)
        pdf_url = upload_pdf(url, url_day_suffix)
        entries = parse_log_pdf(read_pdf, pdf_url)
    
    time.sleep(0.5)
    return entries


# In[31]:


# returns list of log's that aren't present in our database
def get_live_log_dates():
    with open('./data/pulled_logs.json') as f:
        pulled_dates = json.load(f)
    page = requests.get(crime_log_url_addr)
    page_text = BeautifulSoup(page.content)
    option_list = page_text.find_all("option")
    dates = [option["value"] for option in option_list[1:] if option["value"] not in pulled_dates]
    return dates


# In[32]:


def get_logs():
    dates = get_live_log_dates()
    log_data = [log for daily_log in [parse_daily_log(date) for date in dates] for log in daily_log]
    return [log_data, dates]


# In[33]:


def update_data():
    new_data         = get_logs()
    new_log_data     = new_data[0]
    new_pulled_dates = new_data[1]
    print(len(new_log_data))
    print(len(new_pulled_dates))
    with open("./data/pulled_logs_data.json") as f: # read and update
        data = json.load(f)
        data = new_log_data + data
    with open("./data/pulled_logs_data.json", "w") as f: # write changes
        f.seek(0)
        json.dump(data, f)
    with open('./data/pulled_logs.json') as f: # read and update
        pulled_dates = json.load(f)
        pulled_dates = new_pulled_dates + pulled_dates
    with open('./data/pulled_logs.json', "w") as f: # write changes
        f.seek(0)
        json.dump(pulled_dates, f)
    print("SUCCESSFUL UPDATE")


# In[44]:


update_data()


# In[ ]:




