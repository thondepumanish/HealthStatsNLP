/**
 * This class is a controller for the NLPStatistics application.
 * It handles HTTP requests and responses related to NLP statistics.
 */
package com.example.NLPStatistics;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;
import org.springframework.web.client.RestTemplate;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.springframework.ui.Model;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

/**
 * Controller class for handling web page requests and form submissions.
 */
@Controller
public class WebPageController {

    private final String apiEndpoint = "http://localhost:5000/compareStatistics";
    private final ObjectMapper objectMapper = new ObjectMapper();

    @GetMapping("/")
    public String showForm() {
        return "index.html";
    }
    
    @PostMapping("/submit")
    public String handleFormSubmission(@RequestParam("file") MultipartFile file,
                                       @RequestParam("text") String text,
                                       RedirectAttributes redirectAttributes) {
        /**
         * Executes a block of code and handles any exceptions that may occur.
         * 
         * @param codeBlock The block of code to execute.
         */
        try {
            // Prepare the content
            String content;
            if (!file.isEmpty()) {
                content = new String(file.getBytes(), StandardCharsets.UTF_8);
            } else {
                content = text;
            }

            // Create an instance of RestTemplate
            RestTemplate restTemplate = new RestTemplate();

            // Set headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            // Create a request entity
            HttpEntity<String> requestEntity = new HttpEntity<>(content, headers);

            // Send the request and receive a response
            ResponseEntity<String> response = restTemplate.postForEntity(apiEndpoint, requestEntity, String.class);

            // Parse the JSON response
            ObjectMapper objectMapper = new ObjectMapper();
            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);

            // Add the response data to redirectAttributes
            redirectAttributes.addFlashAttribute("value", responseMap);

        } catch (IOException e) {
            e.printStackTrace();
            // Handle the error scenario
            redirectAttributes.addFlashAttribute("errorMessage", "Error processing the file.");
            return "redirect:/errorPage";
        }

        return "redirect:/results";
    }
  
    /**
     * Retrieves and displays the "results" view.
     *
     * @param model The model object used to pass data to the view
     * @return The name of the view to be displayed
     */
    @GetMapping("/results")
    public String showResults(Model model) {
        // No need to manually get flash attributes, Spring automatically adds them to Model
        return "results";
    
    }
}
