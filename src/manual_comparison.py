# Manual comparison between paid traffic and builder program agents

# Paid traffic agents (69 agents)
paid_traffic = {
    "1h24ddd97hrfn8kk", "pdd18pjciy3b0pjb", "w77b59gm4veuvelo", "hletzrnuh0upnj5w", 
    "cs6xru66ss4w29eu", "ns22tqch6lqwwpcw", "z8ddaqxopaz6jdm4", "0rl8poege5wz78jc",
    "k02yqyoxbjdiqcsv", "gp6dbpp6ljitl3i4", "dopy0cq5w4l1v44i", "6rdhln6ukxgt619z",
    "q0md7gxt8du19q9s", "89m8frwlokpxr8ny", "3n42o0s9qdqfn4g9", "2b8i965qh8yqj25p",
    "7u42akwdyvchvqk3", "ntftr74miahjwje7", "7ki89b8dhc5qf5t0", "yxejeenzifyrakf8",
    "yxyqw2wu84ikr71b", "fyqb5rdl0yhrmfht", "ugjb8tv69iy0ro2a", "2a9pjinh94baztv0",
    "n7qrf2vnkjrrsb92", "sdtm8k9uitmfvfzm", "eyg5r22kp5w978jy", "v7hq3ovk3d6tp9tt",
    "754f1tgqoblf0u9h", "i18up3klo8lcwr7x", "plksqcehiaeq3kum", "ixt3dg04kgti4dwz",
    "ce3w5vnp8n7wczms", "9m53pgv1pbjpal33", "1a4g81x0bfsc5dpi", "9kuy7lwvuud9yyzl",
    "ax5no4wtfed7tb47", "w0282qmoaravu6o0", "dg9ygy700kaxfrhs", "xaymmw4g7obsfitc",
    "x1enduxsp3qa1q0i", "z9puf4wjtq69aimh", "9pi17sz4nzggs9qf", "om9fkootmmngoi8h",
    "9whg8euxtsiuxw8b", "k3tzy4olzcs8tl3w", "ee0e6pij4gvw40kj", "tnsjzc0x41how6aa",
    "0gkmdhot7dfusghg", "2b8lokb2buwnb5k9", "mb5x7k7d6owy6zfb", "eqyj3iloqopdt67a",
    "8jchn0bmt9n8lk6g", "9ggs59qppgss54gq", "27c06uk26r8bxwtc", "nhddxyowz7juknrz",
    "a22phtn9ixnonxew", "wx8llcd81iooa7yr", "2bl3mtaj069yluxm", "307gue9rw6h1qq24",
    "ic0v05kkul4t5k6g", "xlodgx8hrmy79bdq", "8cai2azhjjuqccck", "pon27olqoj3z57f7",
    "vxxmvpn1x6afng0f", "wxqzw8nlv9yacnqj", "g6qvb8yw1jujwyh5", "437tseruj5otka7v"
}

# Builder program agents (158 agents) - subset that matters for overlap
builder_program = {
    "a22phtn9ixnonxew", "754f1tgqoblf0u9h", "i18up3klo8lcwr7x", "plksqcehiaeq3kum",
    "wx8llcd81iooa7yr", "0rl8poege5wz78jc", "ns22tqch6lqwwpcw", "pdd18pjciy3b0pjb",
    "w77b59gm4veuvelo", "fyqb5rdl0yhrmfht", "2a9pjinh94baztv0", "27c06uk26r8bxwtc",
    "n7qrf2vnkjrrsb92", "sdtm8k9uitmfvfzm", "eyg5r22kp5w978jy", "9ggs59qppgss54gq",
    "hletzrnuh0upnj5w", "cs6xru66ss4w29eu", "2bl3mtaj069yluxm", "ic0v05kkul4t5k6g",
    "nhddxyowz7juknrz", "ixt3dg04kgti4dwz", "7u42akwdyvchvqk3", "9whg8euxtsiuxw8b",
    "ntftr74miahjwje7", "1h24ddd97hrfn8kk", "k02yqyoxbjdiqcsv", "dopy0cq5w4l1v44i",
    "gp6dbpp6ljitl3i4", "2b8lokb2buwnb5k9", "7ki89b8dhc5qf5t0", "mb5x7k7d6owy6zfb",
    "xlodgx8hrmy79bdq", "8jchn0bmt9n8lk6g", "z9puf4wjtq69aimh", "ee0e6pij4gvw40kj",
    "k3tzy4olzcs8tl3w", "tnsjzc0x41how6aa", "0gkmdhot7dfusghg", "q0md7gxt8du19q9s",
    "89m8frwlokpxr8ny", "2b8i965qh8yqj25p", "3n42o0s9qdqfn4g9", "z8ddaqxopaz6jdm4"
}

# Find overlap
overlap = paid_traffic.intersection(builder_program)
not_in_builder = paid_traffic - builder_program

print(f"Total paid traffic agents: {len(paid_traffic)}")
print(f"Paid traffic agents also in builder program: {len(overlap)}")
print(f"ANSWER: {len(not_in_builder)} paid traffic agents are NOT in builder program")
print(f"Percentage NOT in builder program: {(len(not_in_builder)/len(paid_traffic))*100:.1f}%")

print(f"\nAgents that got paid traffic AND are in builder program:")
for agent_id in sorted(overlap):
    print(f"  {agent_id}") 