package main

import (
	"encoding/csv"
	"errors"
	"fmt"
	"log"
	"os"
	"slices"
)

const (
	dreamJobCsv = "./merged_vacs_2.csv"
	skillsCsv = "./merged_with_original(1).csv"
	outputCsv = "./merged_with_original_skills.csv"
)

func indexOfVacancyByName(header []string, name string) (int, error) {
	for i, h := range header {
		if h == name {
			return i, nil
		}
	}

	return -1, errors.New("column not found")
}

func getCsvRows(csvPath string) ([][]string, error) {
	csvFile, err := os.Open(csvPath)
	if err != nil {
		log.Fatalf("Failed to open CSV file: %v", err)
	}
	defer csvFile.Close()

	csvReader := csv.NewReader(csvFile)
	csvReader.Comma = ','

	rows, err := csvReader.ReadAll()
	if err != nil {
		return nil, err
	}

	return rows, nil
}

func writeCsv(rows [][]string) {
	csvFile, err := os.Create(outputCsv)
	if err != nil {
		log.Fatalf("Failed to create CSV file: %v", err)
	}
	defer csvFile.Close()

	csvWriter := csv.NewWriter(csvFile)
	csvWriter.Comma = ','
	csvWriter.WriteAll(rows)
	csvWriter.Flush()
	if err := csvWriter.Error(); err != nil {
		log.Fatalf("Failed to write CSV file: %v", err)
	}
}

func findVacancyCsv(rows [][]string, id string) ([]string, error) {
	vacancyIdIndex, err := indexOfVacancyByName(rows[0], "id")
	if err != nil {
		log.Fatalf("Vacancy id not found in CSV file")
	}

	for _, row := range rows {
		if row[vacancyIdIndex] == id {
			return row, nil
		}
	}

	return nil, errors.New("vacancy not found")
}

func removeColumns(rows [][]string, columns []string) [][]string {
	var removeColIds []int
	var newRows [][]string
	header := rows[0]
	
	for _, columnName := range columns {
		index, err := indexOfVacancyByName(header, columnName)
		if err != nil {
			fmt.Printf("not found %s\n", columnName)
			continue
		}
		removeColIds = append(removeColIds, index)
	}
	fmt.Printf("removeColIds: %v\n", removeColIds)

	for _, row := range rows {
		var newRow []string
		for colI, col := range row {
			if (slices.Contains(removeColIds, colI)) {
				continue
			}
			newRow = append(newRow, col)
		}
		newRows = append(newRows, newRow)
	}

	return newRows
}

func initColumns(rows [][]string, needColumns []string) [][]string {
	// needColumns := []string{"education", "dreamjob.id", "rating", "recommendation", "employees", "Условия труда", "Уровень дохода", "Коллектив", "Руководство", "Условия для отдыха", "Возможности роста"}
	
	var skippedCols []string
	header := rows[0]
	for _, columnName := range needColumns {
		_, err := indexOfVacancyByName(header, columnName)
		if err != nil {
			skippedCols = append(skippedCols, columnName)
			continue
		}
	}
	
	header = append(header, skippedCols...)
	rows[0] = header

	emptyValues := make([]string, len(skippedCols))
	for i := range emptyValues {
		emptyValues[i] = "" // или любое другое значение по умолчанию
	}

	for i := range rows {
		if i == 0 {
			continue
		}
		rows[i] = append(rows[i], emptyValues...)
	}

	return rows
}

func main() {
	dreamJobRows, err := getCsvRows(dreamJobCsv)
	if err != nil {
		log.Fatalf("Failed to read CSV file: %v", err)
	}
	// dreamJobRows = initColumns(dreamJobRows, []string{"soft_skills", "hard_skills"})
	
	skillRows, err := getCsvRows(skillsCsv)
	if err != nil {
		log.Fatalf("Failed to read CSV file: %v", err)
	}

	softSkillId, err := indexOfVacancyByName(skillRows[0], "soft_skills")
	if err != nil {
		log.Fatalf("Failed to find soft skill id in CSV file: %v", err)
	}

	hardSkillId, err := indexOfVacancyByName(skillRows[0], "hard_skills")
	if err != nil {
		log.Fatalf("Failed to find hard skill id in CSV file: %v", err)
	}

	dreamJobVacId, err := indexOfVacancyByName(dreamJobRows[0], "id")
	if err != nil {
		log.Fatalf("Failed to find dream job id in CSV file: %v", err)
	}

	for i, row := range dreamJobRows {
		if (i == 0) {
			row = append(row, "soft_skills", "hard_skills")
			dreamJobRows[i] = row
			continue
		}
		dreamJobId := row[dreamJobVacId]
		skillRow, err := findVacancyCsv(skillRows, dreamJobId)
		if err != nil {
			log.Fatalf("Failed to find soft row: %v", err)
		}
		
		row = append(row, skillRow[softSkillId], skillRow[hardSkillId])
		dreamJobRows[i] = row
	}
	
	writeCsv(dreamJobRows)
}