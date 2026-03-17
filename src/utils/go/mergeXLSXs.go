package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/xuri/excelize/v2"
)

func main() {
	var dirPath string
	flag.StringVar(&dirPath, "dir", "", "Путь к директории с XLSX файлами")
	flag.Parse()

	if dirPath == "" {
		log.Fatal("Необходимо указать параметр --dir с путем к директории")
	}

	// Нормализуем путь (разрешаем относительные пути)
	dirPath, err := filepath.Abs(dirPath)
	if err != nil {
		log.Fatalf("Ошибка при нормализации пути: %v", err)
	}

	// Проверяем существование директории
	dirInfo, err := os.Stat(dirPath)
	if err != nil {
		log.Fatalf("Ошибка доступа к директории: %v", err)
	}
	if !dirInfo.IsDir() {
		log.Fatalf("Указанный путь не является директорией: %s", dirPath)
	}

	// Находим все XLSX файлы в директории
	xlsxFiles, err := findXLSXFiles(dirPath)
	if err != nil {
		log.Fatalf("Ошибка при поиске XLSX файлов: %v", err)
	}

	if len(xlsxFiles) == 0 {
		// Выводим отладочную информацию
		fmt.Printf("Директория: %s\n", dirPath)
		entries, _ := os.ReadDir(dirPath)
		fmt.Printf("Найдено файлов в директории: %d\n", len(entries))
		for i, entry := range entries {
			if i < 10 { // Показываем первые 10 файлов
				fmt.Printf("  - %s (dir: %v)\n", entry.Name(), entry.IsDir())
			}
		}
		log.Fatal("XLSX файлы не найдены в указанной директории")
	}

	fmt.Printf("Найдено XLSX файлов: %d\n", len(xlsxFiles))

	// Объединяем XLSX файлы
	mergedRows, err := mergeXLSXFiles(xlsxFiles)
	if err != nil {
		log.Fatalf("Ошибка при объединении XLSX файлов: %v", err)
	}

	// Обрабатываем колонку key_skills
	mergedRows, err = processKeySkillsColumn(mergedRows)
	if err != nil {
		log.Fatalf("Ошибка при обработке колонки key_skills: %v", err)
	}

	// Сохраняем результат в той же директории
	outputPath := filepath.Join(dirPath, "merged.xlsx")
	err = writeXLSX(outputPath, mergedRows)
	if err != nil {
		log.Fatalf("Ошибка при записи объединенного XLSX файла: %v", err)
	}

	fmt.Printf("Объединенный XLSX файл создан: %s\n", outputPath)
	fmt.Printf("Всего строк (включая заголовок): %d\n", len(mergedRows))
}

// findXLSXFiles находит все XLSX файлы в указанной директории
func findXLSXFiles(dirPath string) ([]string, error) {
	var xlsxFiles []string

	entries, err := os.ReadDir(dirPath)
	if err != nil {
		return nil, err
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			fileName := strings.ToLower(entry.Name())
			if strings.HasSuffix(fileName, ".xlsx") {
				fullPath := filepath.Join(dirPath, entry.Name())
				xlsxFiles = append(xlsxFiles, fullPath)
			}
		}
	}

	// Сортируем файлы по имени для предсказуемого порядка
	sort.Strings(xlsxFiles)

	return xlsxFiles, nil
}

// mergeXLSXFiles объединяет несколько XLSX файлов в один
// Первый файл читается полностью, остальные - без заголовка
func mergeXLSXFiles(filePaths []string) ([][]string, error) {
	var mergedRows [][]string
	var header []string
	headerWritten := false

	for i, filePath := range filePaths {
		fmt.Printf("Обработка файла %d/%d: %s\n", i+1, len(filePaths), filepath.Base(filePath))

		rows, err := readXLSXFile(filePath)
		if err != nil {
			return nil, fmt.Errorf("ошибка чтения файла %s: %v", filePath, err)
		}

		if len(rows) == 0 {
			fmt.Printf("  Предупреждение: файл пуст, пропускаем\n")
			continue
		}

		// Для первого файла сохраняем заголовок и все строки
		if !headerWritten {
			header = rows[0]
			mergedRows = append(mergedRows, header)
			if len(rows) > 1 {
				mergedRows = append(mergedRows, rows[1:]...)
			}
			headerWritten = true
			fmt.Printf("  Добавлено строк: %d (включая заголовок)\n", len(rows))
		} else {
			// Для остальных файлов пропускаем заголовок
			if len(rows) > 1 {
				mergedRows = append(mergedRows, rows[1:]...)
				fmt.Printf("  Добавлено строк: %d (заголовок пропущен)\n", len(rows)-1)
			} else {
				fmt.Printf("  Предупреждение: файл содержит только заголовок, пропускаем\n")
			}
		}
	}

	return mergedRows, nil
}

// readXLSXFile читает XLSX файл и возвращает все строки из первого листа
func readXLSXFile(filePath string) ([][]string, error) {
	f, err := excelize.OpenFile(filePath)
	if err != nil {
		return nil, err
	}
	defer func() {
		if err := f.Close(); err != nil {
			log.Printf("Ошибка при закрытии файла %s: %v", filePath, err)
		}
	}()

	// Получаем имя первого листа
	sheetName := f.GetSheetName(0)
	if sheetName == "" {
		return nil, fmt.Errorf("файл не содержит листов")
	}

	// Читаем все строки из первого листа
	rows, err := f.GetRows(sheetName)
	if err != nil {
		return nil, err
	}

	return rows, nil
}

// writeXLSX записывает строки в XLSX файл
func writeXLSX(filePath string, rows [][]string) error {
	f := excelize.NewFile()
	defer func() {
		if err := f.Close(); err != nil {
			log.Printf("Ошибка при закрытии файла: %v", err)
		}
	}()

	sheetName := "Sheet1"

	// Записываем строки
	for rowIdx, row := range rows {
		for colIdx, cellValue := range row {
			cellName, err := excelize.CoordinatesToCellName(colIdx+1, rowIdx+1)
			if err != nil {
				return err
			}
			if err := f.SetCellValue(sheetName, cellName, cellValue); err != nil {
				return err
			}
		}
	}

	// Сохраняем файл
	if err := f.SaveAs(filePath); err != nil {
		return err
	}

	return nil
}

// processKeySkillsColumn обрабатывает колонку key_skills, преобразуя JSON в список через запятую
func processKeySkillsColumn(rows [][]string) ([][]string, error) {
	if len(rows) == 0 {
		return rows, nil
	}

	// Находим индекс колонки key_skills
	header := rows[0]
	keySkillsIndex := -1
	for i, colName := range header {
		if colName == "key_skills" {
			keySkillsIndex = i
			break
		}
	}

	// Если колонка не найдена, возвращаем строки без изменений
	if keySkillsIndex == -1 {
		fmt.Printf("Колонка key_skills не найдена, пропускаем обработку\n")
		return rows, nil
	}

	fmt.Printf("Обработка колонки key_skills (индекс: %d)\n", keySkillsIndex)

	// Обрабатываем каждую строку (кроме заголовка)
	processedCount := 0
	for i := 1; i < len(rows); i++ {
		if keySkillsIndex >= len(rows[i]) {
			continue
		}

		cellValue := rows[i][keySkillsIndex]
		if cellValue == "" {
			continue
		}

		// Парсим JSON и извлекаем имена
		processedValue, err := parseKeySkills(cellValue)
		if err != nil {
			// Если не удалось распарсить, оставляем исходное значение
			continue
		}

		// Расширяем строку, если нужно
		for len(rows[i]) <= keySkillsIndex {
			rows[i] = append(rows[i], "")
		}

		rows[i][keySkillsIndex] = processedValue
		processedCount++
	}

	fmt.Printf("Обработано строк с key_skills: %d\n", processedCount)
	return rows, nil
}

// parseKeySkills парсит JSON массив объектов и возвращает список имен через запятую
func parseKeySkills(jsonStr string) (string, error) {
	// Парсим JSON массив
	var skills []map[string]interface{}
	err := json.Unmarshal([]byte(jsonStr), &skills)
	if err != nil {
		return "", err
	}

	// Извлекаем имена
	var names []string
	for _, skill := range skills {
		if name, ok := skill["name"].(string); ok && name != "" {
			names = append(names, name)
		}
	}

	// Объединяем через запятую
	return strings.Join(names, ", "), nil
}
