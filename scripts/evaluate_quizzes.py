import httpx
import json
import re
import collections
import time

API_URL = "http://localhost:14567/api/quiz-session?n=5"
NUM_TESTS = 3
DUMP_FILE = "docs/quiz_test_dump_3x5.md"

def analyze_batch(batch_index, data, file_handle):
    report = []
    report.append(f"\n## BATCH {batch_index + 1}\n")
    
    quizzes = data.get("quizzes", [])
    if not quizzes:
        report.append("No quizzes found in response.")
        file_handle.write("\n".join(report) + "\n")
        return

    all_options = []
    
    for i, quiz in enumerate(quizzes):
        question = quiz.get("question", "")
        options = quiz.get("options", [])
        explanation = quiz.get("explanation", "")
        quiz_type = quiz.get("quiz_type", "unknown")
        
        all_options.extend(options)
        
        leaks = re.findall(r'(?i)(card\s*\d+|source|item\s*\d+)', question)
        handholding = re.findall(r"(?i)(meaning\s*['\"].*?['\"]|means\s*['\"].*?['\"]|significa\s*['\"].*?['\"])", question)
        
        issues = []
        if leaks:
            issues.append(f"LEAK DETECTED: {leaks}")
        if handholding:
            issues.append(f"HAND-HOLDING DETECTED: {handholding}")
            
        report.append(f"### Quiz {i+1} [{quiz_type}]")
        report.append(f"**Q:** {question}")
        for j, opt in enumerate(options):
            report.append(f"{j+1}. {opt}")
        report.append(f"\n**Explanation:** {explanation}\n")
        
        if issues:
            report.append("> [!WARNING]")
            for issue in issues:
                report.append(f"> - {issue}")
        report.append("\n---\n")

    counts = collections.Counter(all_options)
    recycled = {k: v for k, v in counts.items() if v > 1}
    
    if recycled:
        report.append(f"#### Recycled Options:")
        for opt, count in recycled.items():
            report.append(f"- '{opt}' appears {count} times")
    
    file_handle.write("\n".join(report) + "\n")

def main():
    print(f"Iniciando {NUM_TESTS} testes (n=5)... Salvando em {DUMP_FILE}")
    with open(DUMP_FILE, "w", encoding="utf-8") as f:
        f.write("# Dump de Testes - UniversePie (3x5)\n")
        with httpx.Client(timeout=120) as client:
            for i in range(NUM_TESTS):
                print(f"Coletando Batch {i+1}/{NUM_TESTS}...")
                try:
                    response = client.get(API_URL)
                    response.raise_for_status()
                    analyze_batch(i, response.json(), f)
                    print(f"Batch {i+1} salvo com sucesso.")
                except Exception as e:
                    error_msg = f"\nErro ao processar o Batch {i+1}: {e}\n"
                    print(error_msg)
                    f.write(error_msg)
                
                if i < NUM_TESTS - 1:
                    print("Aguardando 25 segundos para resfriamento de RPM...")
                    time.sleep(25)
                    
    print("Processamento concluído.")

if __name__ == '__main__':
    main()
